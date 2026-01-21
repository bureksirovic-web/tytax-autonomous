
const { performance } = require('perf_hooks');

// --- Mock Data & Helpers ---

const normalizeMuscleName = (() => {
    const cache = new Map();
    const rules = [
        { keys: ['CHEST', 'PECTORALIS'], result: 'Chest' },
        { keys: ['LATISSIMUS', 'LATS', 'BACK - VERTICAL'], result: 'Lats' },
        { keys: ['TRAPEZIUS', 'RHOMBOIDS', 'BACK - HORIZONTAL'], result: 'Mid Back' },
        { keys: ['ANTERIOR DELT', 'FRONT DELT'], result: 'Front Delts' },
        { keys: ['LATERAL DELT', 'SIDE DELT'], result: 'Side Delts' },
        { keys: ['POSTERIOR DELT', 'REAR DELT'], result: 'Rear Delts' },
        { keys: ['DELTOID', 'SHOULDER'], result: 'Delts' },
        { keys: ['BICEPS'], result: 'Biceps' },
        { keys: ['TRICEPS'], result: 'Triceps' },
        { keys: ['QUADRICEPS', 'QUADS'], result: 'Quads' },
        { keys: ['HAMSTRINGS'], result: 'Hamstrings' },
        { keys: ['GLUTE', 'GLUTEUS'], result: 'Glutes' },
        { keys: ['CALVES', 'GASTROCNEMIUS', 'SOLEUS'], result: 'Calves' },
        { keys: ['RECTUS ABDOMINIS', 'OBLIQUES', 'CORE'], result: 'Core' },
        { keys: ['FOREARM', 'GRIP'], result: 'Forearms' }
    ];

    return (name) => {
        if (!name) return 'Other';
        if (cache.has(name)) return cache.get(name);

        const n = name.toUpperCase().trim();
        let result = null;

        for (const rule of rules) {
            if (rule.keys.some(k => n.includes(k))) {
                result = rule.result;
                break;
            }
        }

        if (!result) {
            result = name.charAt(0).toUpperCase() + name.slice(1).toLowerCase();
        }

        cache.set(name, result);
        return result;
    };
})();

const REGEX_LEVEL = /(Primary|Secondary|Tertiary)/i;
const REGEX_SCORE = /(\d+)/;
const REGEX_CLEAN_CHARS = /[~>]/g;
const REGEX_CLEAN_PHRASE = /keep it light\/clean/i;

const parseImpact = (note) => {
    if (!note) return [];
    const impacts = [];
    const segments = note.split(';');
    segments.forEach(segment => {
        const cleanSeg = segment.trim();
        const levelMatch = cleanSeg.match(REGEX_LEVEL);
        const scoreMatch = cleanSeg.match(REGEX_SCORE);

        if (levelMatch && scoreMatch) {
            let muscle = cleanSeg
                .replace(levelMatch[0], '')
                .replace(scoreMatch[0], '')
                .replace(REGEX_CLEAN_CHARS, '')
                .replace(REGEX_CLEAN_PHRASE, '')
                .trim();

            if (muscle) {
                impacts.push({
                    level: levelMatch[0],
                    score: parseInt(scoreMatch[0]),
                    muscle: muscle.toLowerCase()
                });
            }
        }
    });
    return impacts;
};

const getImpact = (exercise) => {
    if (exercise.impact && Array.isArray(exercise.impact)) {
        return exercise.impact.map(i => ({
            muscle: normalizeMuscleName(i.m),
            score: i.s,
            level: i.s >= 90 ? 'Primary' : i.s >= 50 ? 'Secondary' : 'Tertiary'
        }));
    }
    if (exercise.impact && typeof exercise.impact === 'object') {
            return Object.entries(exercise.impact).map(([k, v]) => ({
                muscle: normalizeMuscleName(k),
                score: v,
                level: v >= 90 ? 'Primary' : v >= 50 ? 'Secondary' : 'Tertiary'
            }));
    }
    return parseImpact(exercise.note);
};

const calculateImpactDistribution = (exercises, useRealData = false, userBodyweight = 75) => {
    const impact = {};
    exercises.forEach(ex => {
        let load = 0;

        if (useRealData && ex.sets) {
            ex.sets.forEach(s => {
                if (s.done || (s.kg && s.reps)) {
                        let w = parseFloat(s.kg);
                        if (isNaN(w) || w === 0) w = userBodyweight || 75;
                        let r = parseFloat(s.reps) || 0;
                        load += (w * r);
                }
            });
        } else {
            load = useRealData ? (ex.sets ? ex.sets.length : 1) : 1;
        }

        if (ex.unilateral) load *= 2;

        if (load > 0) {
            const parsed = getImpact(ex);
            parsed.forEach(p => {
                impact[p.muscle] = (impact[p.muscle] || 0) + (p.score * load);
            });
        }
    });

    const values = Object.values(impact);
    const max = values.length ? Math.max(...values) : 1;

    return Object.entries(impact)
        .sort((a, b) => b[1] - a[1])
        .map(([m, s]) => ({ muscle: m, score: s, pct: (s / max) * 100 }));
};

// --- Benchmark ---

// Mock specific exercises (mixed legacy note-based and new format)
const mockExercises = [];
for (let i = 0; i < 20; i++) { // Typical workout size
    mockExercises.push({
        name: `Exercise ${i}`,
        sets: [
            { kg: 100, reps: 10, done: true },
            { kg: 100, reps: 10, done: true },
            { kg: 100, reps: 10, done: true }
        ],
        unilateral: i % 2 === 0,
        // Mix of formats
        impact: i % 2 === 0 ? [ { m: 'Chest', s: 90 }, { m: 'Triceps', s: 50 } ] : null,
        note: i % 2 !== 0 ? "Primary Chest 90; Secondary Triceps 50" : ""
    });
}

console.log("Starting Benchmark: calculateImpactDistribution");
console.log(`Exercises: ${mockExercises.length}`);

// Baseline: 11 calls per render (1 for main panel, 10 for sticky dock)
const ITERATIONS = 1000; // Simulate 1000 renders (e.g., 16 minutes of workout timer)
const CALLS_PER_RENDER = 11;

const startUnoptimized = performance.now();
for (let i = 0; i < ITERATIONS; i++) {
    for (let j = 0; j < CALLS_PER_RENDER; j++) {
        calculateImpactDistribution(mockExercises, true, 80);
    }
}
const endUnoptimized = performance.now();
const timeUnoptimized = endUnoptimized - startUnoptimized;

// Optimized: 1 call per render (memoized)
const startOptimized = performance.now();
for (let i = 0; i < ITERATIONS; i++) {
    // Memoization check simulation: only calc once
    const result = calculateImpactDistribution(mockExercises, true, 80);
    // Reuse result 10 times (negligible cost)
    for (let j = 0; j < 10; j++) {
        const _ = result;
    }
}
const endOptimized = performance.now();
const timeOptimized = endOptimized - startOptimized;

console.log(`\nResults (${ITERATIONS} renders):`);
console.log(`Unoptimized (11 calls/render): ${timeUnoptimized.toFixed(2)}ms`);
console.log(`Optimized (1 call/render):     ${timeOptimized.toFixed(2)}ms`);
console.log(`Improvement: ${(timeUnoptimized / timeOptimized).toFixed(1)}x faster`);

const perRenderSaving = (timeUnoptimized - timeOptimized) / ITERATIONS;
console.log(`\nTime saved per render: ${perRenderSaving.toFixed(3)}ms`);
