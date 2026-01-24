const fs = require('fs');
const path = require('path');

// Mock window
const window = {};

// Load Data
const dataPath = path.join(__dirname, '../full_exercises_final.js');
const dataContent = fs.readFileSync(dataPath, 'utf8');
eval(dataContent); // Populates window.TYTAX_MAINFRAME

const exercises = window.TYTAX_MAINFRAME;
console.log(`Loaded ${exercises.length} exercises.`);

// --- ORIGINAL FUNCTIONS FROM index.html ---

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

// ORIGINAL getImpact (Unoptimized)
const getImpact_Original = (exercise) => {
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

// OPTIMIZED getImpact
const getImpact_Optimized = (() => {
    const cache = new WeakMap();
    return (exercise) => {
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

// --- BENCHMARK ---

const ITERATIONS = 100;

console.log(`Benchmarking ${ITERATIONS} iterations over ${exercises.length} exercises...`);

// Test Original
const startOriginal = performance.now();
for (let i = 0; i < ITERATIONS; i++) {
    for (const ex of exercises) {
        getImpact_Original(ex);
    }
}
const endOriginal = performance.now();
console.log(`Original Time: ${(endOriginal - startOriginal).toFixed(2)}ms`);

// Test Optimized
const startOptimized = performance.now();
for (let i = 0; i < ITERATIONS; i++) {
    for (const ex of exercises) {
        getImpact_Optimized(ex);
    }
}
const endOptimized = performance.now();
console.log(`Optimized Time: ${(endOptimized - startOptimized).toFixed(2)}ms`);

const speedup = (endOriginal - startOriginal) / (endOptimized - startOptimized);
console.log(`Speedup: ${speedup.toFixed(2)}x`);
