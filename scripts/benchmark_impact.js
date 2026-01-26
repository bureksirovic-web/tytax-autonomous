
// Mock global window and environment
global.window = {};

// --- HELPER FUNCTIONS (From index.html) ---
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

// Hoisted Regexes for Performance
const REGEX_LEVEL = /(Primary|Secondary|Tertiary)/i;
const REGEX_SCORE = /(\d+)/;
const REGEX_CLEAN_CHARS = /[~>]/g;
const REGEX_CLEAN_PHRASE = /keep it light\/clean/i;

const parseImpact = (note) => {
    if (!note) return [];
    const impacts = [];

    // New logic: Split by semicolon and parse each segment flexibly
    const segments = note.split(';');
    segments.forEach(segment => {
        const cleanSeg = segment.trim();
        // Regex to find "Primary", "Secondary", or "Tertiary" (case insensitive)
        const levelMatch = cleanSeg.match(REGEX_LEVEL);
        // Regex to find the score (digits)
        const scoreMatch = cleanSeg.match(REGEX_SCORE);

        if (levelMatch && scoreMatch) {
            // Extract muscle name: remove level, score, special chars like ~
            let muscle = cleanSeg
                .replace(levelMatch[0], '')
                .replace(scoreMatch[0], '')
                .replace(REGEX_CLEAN_CHARS, '')
                .replace(REGEX_CLEAN_PHRASE, '') // Specific cleanup for known noisy notes
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

// Current Implementation
const getImpact = (exercise) => {
    // Check for v2.1 structured impact (Array)
    if (exercise.impact && Array.isArray(exercise.impact)) {
        return exercise.impact.map(i => ({
            muscle: normalizeMuscleName(i.m),
            score: i.s,
            level: i.s >= 90 ? 'Primary' : i.s >= 50 ? 'Secondary' : 'Tertiary'
        }));
    }
    // Check for v3.0 structured impact (Object)
    if (exercise.impact && typeof exercise.impact === 'object') {
            return Object.entries(exercise.impact).map(([k, v]) => ({
                muscle: normalizeMuscleName(k),
                score: v,
                level: v >= 90 ? 'Primary' : v >= 50 ? 'Secondary' : 'Tertiary'
            }));
    }
    // Fallback to old string-based note parsing
    return parseImpact(exercise.note);
};

// Optimized Implementation
const getImpactOptimized = (() => {
    const cache = new WeakMap();
    return (exercise) => {
        if (!exercise) return [];
        if (cache.has(exercise)) return cache.get(exercise);

        let result;
        // Check for v2.1 structured impact (Array)
        if (exercise.impact && Array.isArray(exercise.impact)) {
            result = exercise.impact.map(i => ({
                muscle: normalizeMuscleName(i.m),
                score: i.s,
                level: i.s >= 90 ? 'Primary' : i.s >= 50 ? 'Secondary' : 'Tertiary'
            }));
        }
        // Check for v3.0 structured impact (Object)
        else if (exercise.impact && typeof exercise.impact === 'object') {
                result = Object.entries(exercise.impact).map(([k, v]) => ({
                    muscle: normalizeMuscleName(k),
                    score: v,
                    level: v >= 90 ? 'Primary' : v >= 50 ? 'Secondary' : 'Tertiary'
                }));
        }
        // Fallback to old string-based note parsing
        else {
            result = parseImpact(exercise.note);
        }

        cache.set(exercise, result);
        return result;
    };
})();


// --- MOCK DATA ---
// Create a large dataset similar to TYTAX_MAINFRAME
const MOCK_DATA_SIZE = 5000;
const mockExercises = [];
const patterns = [
    { impact: [{ m: 'Chest', s: 95 }, { m: 'Triceps', s: 60 }] }, // Array format
    { impact: { 'Lats': 90, 'Biceps': 50 } }, // Object format
    { note: "Primary Chest 90; Secondary Triceps 50" }, // Note format
    { note: "" } // Empty
];

for (let i = 0; i < MOCK_DATA_SIZE; i++) {
    const pattern = patterns[i % patterns.length];
    mockExercises.push({
        id: i,
        name: `Exercise ${i}`,
        ...pattern
    });
}

// --- BENCHMARK ---
console.log(`Benchmarking with ${MOCK_DATA_SIZE} exercises...`);

// Test 1: Original implementation
const start1 = performance.now();
for (let j = 0; j < 100; j++) { // Simulate 100 renders/filters
    for (let i = 0; i < MOCK_DATA_SIZE; i++) {
        getImpact(mockExercises[i]);
    }
}
const end1 = performance.now();
console.log(`Original getImpact: ${(end1 - start1).toFixed(2)}ms`);

// Test 2: Optimized implementation (First pass - Cold Cache)
const start2 = performance.now();
for (let i = 0; i < MOCK_DATA_SIZE; i++) {
    getImpactOptimized(mockExercises[i]);
}
const end2 = performance.now();
console.log(`Optimized getImpact (Cold Cache): ${(end2 - start2).toFixed(2)}ms`);

// Test 3: Optimized implementation (Subsequent passes - Warm Cache)
const start3 = performance.now();
for (let j = 0; j < 100; j++) {
    for (let i = 0; i < MOCK_DATA_SIZE; i++) {
        getImpactOptimized(mockExercises[i]);
    }
}
const end3 = performance.now();
console.log(`Optimized getImpact (Warm Cache - 100 iterations): ${(end3 - start3).toFixed(2)}ms`);

const improvement = ((end1 - start1) - (end3 - start3)) / (end1 - start1) * 100;
console.log(`Improvement (Warm Cache vs Original): ${improvement.toFixed(2)}%`);
