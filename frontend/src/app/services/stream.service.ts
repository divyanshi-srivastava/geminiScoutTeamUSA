import { Injectable, NgZone } from '@angular/core';
import { Observable } from 'rxjs';
import { StateService } from './state.service';
import { Question, Profile, ScoutChunk, ScoutingResult } from '../models';
import { environment } from '../../environments/environment';

/**
 * Local pathway manifest for enriching single-profile Scout results
 * with distinct Olympic/Paralympic disciplines.
 */
const PATHWAY_MANIFEST: Record<number, { standing: string; adaptive: string }> = {
  1:  { standing: 'Elite Artistic Gymnastics', adaptive: 'Elite Adaptive Swimming (e.g., Women\'s 100 m Freestyle S6)' },
  2:  { standing: 'Elite Distance Running', adaptive: 'Elite Wheelchair Racing (e.g., Women\'s Marathon T54)' },
  3:  { standing: 'Elite Sprint / Jumping', adaptive: 'Elite Para Athletics (e.g., Long Jump T64)' },
  4:  { standing: 'Elite Swimming', adaptive: 'Elite Para Swimming (e.g., 100 m Breaststroke SB14)' },
  5:  { standing: 'Elite Court / Racket Sports', adaptive: 'Elite Wheelchair Tennis' },
  6:  { standing: 'Elite Wrestling / Grappling', adaptive: 'Elite Para Judo / Powerlifting' },
  7:  { standing: 'Elite Throwing / Field Events', adaptive: 'Elite Para Shot Put (e.g., F57)' },
  8:  { standing: 'Elite Rowing / Paddling', adaptive: 'Elite Para Rowing (e.g., PR3 Mixed Coxed Four)' },
  9:  { standing: 'Elite Combat Sports', adaptive: 'Elite Wheelchair Fencing' },
  10: { standing: 'Elite Team Ball Sports', adaptive: 'Elite Wheelchair Basketball / Sitting Volleyball' },
  11: { standing: 'Elite Cycling', adaptive: 'Elite Para Cycling (Handcycling)' },
  12: { standing: 'Elite Winter Sports', adaptive: 'Elite Para Alpine Skiing' },
};

@Injectable({
  providedIn: 'root'
})
export class StreamService {
  constructor(
    private zone: NgZone,
    private state: StateService
  ) {}

  consume(body: any): Observable<void> {
    const url = `${environment.apiUrl}/scout`;

    return new Observable(observer => {
      fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      }).then(async response => {
        if (!response.ok) {
          this.zone.run(() => observer.error(`HTTP ${response.status}`));
          return;
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (reader) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const segments = buffer.split('\n\n');
          buffer = segments.pop() || '';

          for (const segment of segments) {
            const lines = segment.split('\n');
            for (const line of lines) {
              if (!line.startsWith('data: ')) continue;
              const raw = line.substring(6).trim();
              if (raw === '[DONE]') continue;

              try {
                const chunk = JSON.parse(raw);
                this.zone.run(() => this.dispatch(chunk));
              } catch (e) {
                console.warn('[StreamService] Non-JSON line ignored:', raw);
              }
            }
          }
        }
        this.zone.run(() => observer.complete());
      }).catch(err => {
        this.zone.run(() => observer.error(err));
      });
    });
  }

  /**
   * Central dispatcher: routes each SSE chunk to the right state handler
   * based on its `type` field.
   */
  private dispatch(chunk: ScoutChunk): void {
    switch (chunk.type) {
      case 'trace':
        this.state.addTrace(chunk);
        break;

      case 'interview':
        this.handleInterview(chunk.response);
        break;

      case 'result':
        this.handleResult(chunk.response);
        break;

      case 'error':
        console.error('[StreamService] Backend error:', chunk.detail);
        break;
    }
  }

  /**
   * Parse the Narrator's interview response.
   * 
   * CRITICAL: The backend tags ALL responses from INTERVIEW-mode requests as
   * type:"interview", even when the Supervisor internally completed the full
   * scouting pipeline. We must detect result-shaped payloads here and reroute
   * them to handleResult() instead of rendering them as questions.
   */
  private handleInterview(raw: string): void {
    const data = this.extractJson<any>(raw);

    // ── Discriminated Parsing ──
    if (this.looksLikeResult(data)) {
      this.state.addTrace({
        type: 'trace',
        agent: 'system',
        event: 'ScoutingDetected',
        timestamp: new Date().toLocaleTimeString(),
        detail: 'Scouting result detected inside interview stream. Transitioning to Report.'
      });
      // Show narrative bridge briefly before transitioning
      this.state.setNarrativeBridge(
        'The Narrator is weaving your Team USA legacy from the data...'
      );
      // Delay the result transition so the bridge is visible
      setTimeout(() => {
        this.zone.run(() => this.handleResult(raw));
      }, 2500);
      return;
    }

    // ── Normal Question Handling ──
    if (data && data.question) {
      this.state.setActiveQuestion({
        feedback: data.feedback || '',
        question: data.question,
        options: data.options || []
      });
    } else {
      // Defensive Parser: Fallback to plain text
      this.state.addTrace({
        type: 'trace',
        agent: 'system',
        event: 'ParserWarning',
        timestamp: new Date().toLocaleTimeString(),
        detail: 'Interview response fell back to plain text display.'
      });

      this.state.setActiveQuestion({
        feedback: '',
        question: raw,
        options: []
      });
    }
  }

  /**
   * STRICT shape detector: returns true ONLY if the parsed data is
   * unambiguously a scouting result, not an interview question.
   */
  private looksLikeResult(data: any): boolean {
    if (!data) return false;

    // If it has a "question" field, it's an interview question — never a result
    if (data.question) return false;

    // Single profile: require BOTH fields together (strict)
    if (data.matched_profile_name && data.scout_verdict) {
      return true;
    }

    // Structured ScoutingResult with distinct pathways
    if (data.olympic || data.paralympic) {
      return true;
    }

    // Array of profiles (both must have the name field)
    if (Array.isArray(data) && data.length > 0 && data[0].matched_profile_name && data[0].scout_verdict) {
      return true;
    }

    return false;
  }

  /**
   * Parse the final scouting result and ENRICH it with pathway data
   * from the local pathway_manifest.
   */
  private handleResult(raw: string): void {
    const data = this.extractJson<any>(raw);
    
    let result: ScoutingResult;

    if (Array.isArray(data) && data.length > 0) {
      // Two distinct profiles from backend (or fallback if only one provided)
      result = {
        olympic: this.enrichProfile(data[0], 'standing'),
        paralympic: this.enrichProfile(data[1] || data[0], 'adaptive'),
        overall_narrative: 'Your physical metrics and narrative history reveal two powerful pathways for your Team USA legacy.'
      };
    } else if (data && (data.olympic || data.primary || data.archetypes)) {
      // Structured ScoutingResult from backend
      result = {
        olympic: this.enrichProfile(data.olympic || data.primary || data.archetypes?.[0], 'standing'),
        paralympic: this.enrichProfile(data.paralympic || data.secondary || data.archetypes?.[1] || data.olympic || data.primary, 'adaptive'),
        overall_narrative: data.overall_narrative || data.narrative || 'A comprehensive analysis of your athletic potential.'
      };
    } else if (data && data.matched_profile_name && data.scout_verdict) {
      // Single profile from Scout Agent — split into Olympic + Paralympic
      const enriched = this.enrichProfile(data);
      const manifestEntry = PATHWAY_MANIFEST[data.matched_profile_id];

      const olympicProfile: Profile = {
        ...enriched,
        pathway_standing: manifestEntry?.standing || enriched.pathway_standing,
      };

      const paralympicProfile: Profile = {
        ...enriched,
        matched_profile_name: enriched.matched_profile_name,
        scout_verdict: manifestEntry?.adaptive 
          ? `Your physical profile aligns with ${manifestEntry.adaptive}. This adaptive discipline leverages the same core strengths identified in your archetype — demonstrating that elite athletic potential exists across all pathways.`
          : enriched.scout_verdict,
        pathway_adaptive: manifestEntry?.adaptive || enriched.pathway_adaptive,
      };

      result = {
        olympic: olympicProfile,
        paralympic: paralympicProfile,
        overall_narrative: enriched.scout_verdict
      };
    } else {
      // Defensive Parser
      this.state.addTrace({
        type: 'trace',
        agent: 'system',
        event: 'ParserWarning',
        timestamp: new Date().toLocaleTimeString(),
        detail: 'Result JSON failed to parse. Displaying raw output.'
      });

      const fallback: Profile = {
        matched_profile_id: 0,
        matched_profile_name: 'Analysis Result',
        scout_verdict: 'Review your personalized narrative below.',
        life_stage: 'Elite Peak'
      };
      result = { 
        olympic: fallback, 
        paralympic: fallback,
        overall_narrative: raw 
      };
    }

    this.state.setResult(result);
    this.state.setAppState('RESULT');
  }

  /**
   * Enriches a raw profile from the Scout Agent with pathway data
   * from the local pathway_manifest.json.
   * `preferredPathway` specifies whether we want the standing or adaptive discipline string.
   */
  private enrichProfile(profile: any, preferredPathway?: 'standing' | 'adaptive'): Profile {
    if (!profile) {
      return {
        matched_profile_id: 0,
        matched_profile_name: 'Unknown',
        scout_verdict: '',
        life_stage: 'Elite Peak'
      };
    }

    const manifestEntry = PATHWAY_MANIFEST[profile.matched_profile_id];
    
    // Default to enriching both, but if preferredPathway is passed, make sure it is set.
    return {
      matched_profile_id: profile.matched_profile_id || 0,
      matched_profile_name: profile.matched_profile_name || 'Your Archetype',
      scout_verdict: profile.scout_verdict || '',
      life_stage: profile.life_stage || 'Elite Peak',
      pathway_standing: profile.pathway_standing || manifestEntry?.standing || undefined,
      pathway_adaptive: profile.pathway_adaptive || manifestEntry?.adaptive || undefined,
    };
  }

  /**
   * Robust JSON extractor: handles raw JSON, markdown-fenced JSON,
   * nested JSON within prose text, and arrays of JSON objects.
   */
  private extractJson<T>(raw: string): any {
    // 1. Try direct parse
    try {
      return JSON.parse(raw);
    } catch {}

    // 2. Try extracting from ALL ```json ... ``` fences
    const fenceRegex = /```(?:json)?\s*([\s\S]*?)```/g;
    const fenceMatches = [...raw.matchAll(fenceRegex)];
    if (fenceMatches.length > 0) {
      const results = fenceMatches.map(m => {
        try { return JSON.parse(m[1].trim()); } catch { return null; }
      }).filter(x => x !== null);
      
      if (results.length > 1) return results;
      if (results.length === 1) return results[0];
    }

    // 3. Try finding the LARGEST valid JSON array (greedy)
    const arrayStart = raw.indexOf('[');
    const arrayEnd = raw.lastIndexOf(']');
    if (arrayStart !== -1 && arrayEnd > arrayStart) {
      try {
        const arr = JSON.parse(raw.substring(arrayStart, arrayEnd + 1));
        if (Array.isArray(arr)) return arr;
      } catch {}
    }

    // 4. Try finding the LARGEST valid JSON object (greedy)
    const braceStart = raw.indexOf('{');
    const braceEnd = raw.lastIndexOf('}');
    if (braceStart !== -1 && braceEnd > braceStart) {
      try {
        return JSON.parse(raw.substring(braceStart, braceEnd + 1));
      } catch {}
    }

    // 5. Fallback: non-greedy individual objects. If multiple found, return as an array!
    const braceRegex = /\{[\s\S]*?\}/g;
    const braceMatches = raw.match(braceRegex);
    if (braceMatches && braceMatches.length > 0) {
      const results = braceMatches.map(m => {
        try { return JSON.parse(m); } catch { return null; }
      }).filter(x => x !== null);

      if (results.length > 1) return results; // Returns the array of profiles!
      if (results.length === 1) return results[0];
    }

    return null;
  }
}
