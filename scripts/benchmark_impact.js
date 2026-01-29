const { performance } = require('perf_hooks');
const fs = require('fs');

// Mock window and other globals
global.window = {};
const fileContent = fs.readFileSync('full_exercises_final.js', 'utf8');
eval(fileContent); // Load TYTAX_MAINFRAME

const mainframe = window.TYTAX_MAINFRAME;
console.log('Mainframe size:', mainframe.length);

// Mock helpers
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

// Target function
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

// Optimized version
const IMPACT_CACHE = new WeakMap();
const getImpactOptimized = (exercise) => {
    if (IMPACT_CACHE.has(exercise)) return IMPACT_CACHE.get(exercise);

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

    IMPACT_CACHE.set(exercise, result);
    return result;
};

// Benchmark
const iterations = 100; // Simulate filtering multiple times
const start = performance.now();
for (let i = 0; i < iterations; i++) {
    mainframe.forEach(ex => getImpact(ex));
}
const end = performance.now();
console.log('Original time:', (end - start).toFixed(2), 'ms');

const startOpt = performance.now();
for (let i = 0; i < iterations; i++) {
    mainframe.forEach(ex => getImpactOptimized(ex));
}
const endOpt = performance.now();
console.log('Optimized time:', (endOpt - startOpt).toFixed(2), 'ms');
