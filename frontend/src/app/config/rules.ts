export const Rules = {
  limits: {
    minAge: 16,
    peakStart: 20,
    peakEnd: 32,
    maxAge: 55,
  },
  timeline: {
    getAgePhase: (age: number) => {
      if (age < 20) return { label: 'Rising Star', color: '#34d399' };
      if (age <= 32) return { label: 'Elite Peak', color: '#facc15' };
      if (age <= 45) return { label: 'Veteran', color: '#60a5fa' };
      return { label: 'Legacy Coach', color: '#a78bfa' };
    }
  }
};
