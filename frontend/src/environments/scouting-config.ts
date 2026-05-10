export const ScoutingConfig = {
    // ── TEMPORAL CONSTRAINTS ──
    // Mirrored from system_constraints.json
    limits: {
        minAge: 16,     // The "Rising Star" threshold
        peakStart: 20,  // Centroids are most accurate here
        peakEnd: 32,
        maxAge: 55,     // The "Legacy/Coach" threshold
    },

    // ── PHYSICAL SANITY CHECKS ──
    validation: {
        height: { min: 120, max: 220, unit: 'cm' },
        weight: { min: 40, max: 200, unit: 'kg' }
    },

    // ── TIMELINE LOGIC ──
    // This logic determines which games appear in the "Time Travel" bar
    timeline: {
        getEligibleGames: (birthYear: number, gamesManifest: any[]) => {
            return gamesManifest.filter(game => {
                const ageAtGame = game.year - birthYear;
                return ageAtGame >= ScoutingConfig.limits.minAge &&
                    ageAtGame <= ScoutingConfig.limits.maxAge;
            });
        },

        // ── STATE PIVOTS ──
        // How the UI labels the timeline points based on age
        getAgePhase: (age: number) => {
            if (age < 20) return { label: 'Rising Star', color: '#34d399' }; // Green
            if (age <= 32) return { label: 'Elite Peak', color: '#facc15' };  // Gold
            if (age <= 45) return { label: 'Veteran', color: '#60a5fa' };     // Blue
            return { label: 'Legacy Coach', color: '#a78bfa' };               // Purple
        }
    }
};