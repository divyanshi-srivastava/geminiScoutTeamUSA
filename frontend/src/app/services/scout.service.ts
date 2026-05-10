import { Injectable, NgZone } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';
import { Observable } from 'rxjs';

// Data imports for local matching logic
import legacyFactsData from '../../assets/data/legacy_facts.json';
import pathwayManifestData from '../../assets/data/pathway_manifest.json';

/**
 * CORE INTERFACES
 */
export interface ScoutRequest {
  birthYear: number;
  height_cm: number;
  weight_kg: number;
  userStory: string;
}

export interface AgentTrace {
  agent: string;
  event: string;
  timestamp: string;
  detail?: string;
}

export interface ScoutResponse {
  response: string;
  trace: AgentTrace[];
}

export interface LegacyFact {
  year: number;
  sport: string;
  fact_story: string;
  citation_note?: string;
  source_credit?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ScoutService {
  private apiUrl = environment.apiUrl;
  private facts: LegacyFact[] = (legacyFactsData as any);
  private manifest: any[] = (pathwayManifestData as any);

  constructor(private http: HttpClient, private ngZone: NgZone) { }

  /**
   * Primary Scouting Pipeline
   * Handles multi-agent streaming from the FastAPI backend.
   */
  scoutProspect(data: ScoutRequest): Observable<any> {
    const payload = {
      story: data.userStory,
      user_id: `user_${Date.now()}`,
      session_id: `session_${Date.now()}`,
      height_cm: data.height_cm,
      weight_kg: data.weight_kg,
      birth_year: data.birthYear
    };

    return new Observable(observer => {
      fetch(`${this.apiUrl}/scout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      }).then(async response => {
        console.log('📡 [NETWORK] Connection Established:', response.status);

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          this.ngZone.run(() => observer.error('No reader available'));
          return;
        }

        let buffer = '';
        while (true) {
          const { value, done } = await reader.read();
          if (done) {
            console.log('🏁 [STREAM] Connection closed by server.');
            break;
          }

          const rawChunk = decoder.decode(value, { stream: true });
          console.log('📥 [RAW CHUNK]:', rawChunk);

          buffer += rawChunk;
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed || trimmed.startsWith(':')) continue;

            // 1. Handle the finish signal
            if (trimmed.includes('[DONE]')) {
              this.ngZone.run(() => observer.complete());
              return;
            }

            // 2. THE UNIVERSAL PARSER: Handle lines with OR without "data: " prefix
            const jsonPart = trimmed.startsWith('data: ') ? trimmed.substring(6) : trimmed;

            try {
              const chunk = JSON.parse(jsonPart);

              // FORCE TYPE: If it has a response, it's a result. Period.
              if (!chunk.type && chunk.response) {
                chunk.type = 'result';
              }

              console.log('🚀 [SERVICE] Emitting chunk:', chunk);
              this.ngZone.run(() => observer.next(chunk));
            } catch (e) {
              // Partial JSON, wait for next buffer
              buffer = line + '\n' + buffer;
            }
          }
        }

        this.ngZone.run(() => observer.complete());
      }).catch(err => {
        console.error('💥 [FATAL] Stream Error:', err);
        this.ngZone.run(() => observer.error(err));
      });
    });
  }

  /**
   * UI HELPER METHODS
   */
  getRandomFact(): LegacyFact {
    return this.facts[Math.floor(Math.random() * this.facts.length)];
  }

  getArchetype(id: number): any {
    return this.manifest.find(a => a.id === id) || null;
  }
}