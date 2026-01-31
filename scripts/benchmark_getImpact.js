const { performance } = require('perf_hooks');
const assert = require('assert');

// --- MOCKS ---

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

// --- IMPLEMENTATIONS ---

const getImpact_Current = (exercise) => {
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

const getImpact_Optimized = (() => {
    const cache = new WeakMap();
    return (exercise) => {
        if (!exercise) return [];
        if (cache.has(exercise)) return cache.get(exercise);

        let result;
        if (exercise.impact && Array.isArray(exercise.impact)) {
            result = exercise.impact.map(i => ({
                muscle: normalizeMuscleName(i.m),
                score: i.s,
                level: i.s >= 90 ? 'Primary' : i.s >= 50 ? 'Secondary' : 'Tertiary'
            }));
        } else if (exercise.impact && typeof exercise.impact === 'object') {
            result = Object.entries(exercise.impact).map(([k, v]) => ({
                muscle: normalizeMuscleName(k),
                score: v,
                level: v >= 90 ? 'Primary' : v >= 50 ? 'Secondary' : 'Tertiary'
            }));
        } else {
            result = parseImpact(exercise.note);
        }

        cache.set(exercise, result);
        return result;
    };
})();

// --- DATA GENERATION ---

console.log("Generating dataset...");
const dataset = [];
const DATA_SIZE = 5000;

const sampleNotes = [
    "Primary Chest 95; Secondary Triceps 60",
    "Primary Lats 90; Secondary Biceps 50",
    "Primary Quads 95",
    "Primary Glutes 95; Secondary Hamstrings 75"
];

for (let i = 0; i < DATA_SIZE; i++) {
    const type = i % 3;
    if (type === 0) {
        // v2.1 Array
        dataset.push({
            impact: [
                { m: 'Chest', s: 95 },
                { m: 'Triceps', s: 65 }
            ]
        });
    } else if (type === 1) {
        // v3.0 Object
        dataset.push({
            impact: {
                'Chest': 95,
                'Triceps': 65
            }
        });
    } else {
        // Note based
        dataset.push({
            note: sampleNotes[i % sampleNotes.length]
        });
    }
}

// --- VERIFICATION ---
console.log("Verifying correctness...");
dataset.forEach((ex, i) => {
    const res1 = getImpact_Current(ex);
    const res2 = getImpact_Optimized(ex);
    try {
        assert.deepStrictEqual(res1, res2);
    } catch (e) {
        console.error("Verification failed at index", i);
        console.error("Current:", res1);
        console.error("Optimized:", res2);
        process.exit(1);
    }
});
console.log("Verification passed.");

// --- BENCHMARK ---
const RENDER_CYCLES = 100; // Simulate 100 re-renders of the list
console.log(`Starting benchmark: ${DATA_SIZE} items, ${RENDER_CYCLES} render cycles...`);

// Current
const start1 = performance.now();
for (let i = 0; i < RENDER_CYCLES; i++) {
    dataset.forEach(ex => getImpact_Current(ex));
}
const end1 = performance.now();
const time1 = end1 - start1;

// Optimized
const start2 = performance.now();
for (let i = 0; i < RENDER_CYCLES; i++) {
    dataset.forEach(ex => getImpact_Optimized(ex));
}
const end2 = performance.now();
const time2 = end2 - start2;

console.log(`Current:   ${time1.toFixed(2)} ms`);
console.log(`Optimized: ${time2.toFixed(2)} ms`);
console.log(`Improvement: ${((time1 - time2) / time1 * 100).toFixed(2)}%`);
