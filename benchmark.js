
const assert = require('assert');
const { performance } = require('perf_hooks');

// --- 1. CURRENT IMPLEMENTATION ---
const parseImpact_Current = (note) => {
    if (!note) return [];
    const impacts = [];

    // New logic: Split by semicolon and parse each segment flexibly
    const segments = note.split(';');
    segments.forEach(segment => {
        const cleanSeg = segment.trim();
        // Regex to find "Primary", "Secondary", or "Tertiary" (case insensitive)
        const levelMatch = cleanSeg.match(/(Primary|Secondary|Tertiary)/i);
        // Regex to find the score (digits)
        const scoreMatch = cleanSeg.match(/(\d+)/);

        if (levelMatch && scoreMatch) {
            // Extract muscle name: remove level, score, special chars like ~
            let muscle = cleanSeg
                .replace(levelMatch[0], '')
                .replace(scoreMatch[0], '')
                .replace(/[~>]/g, '')
                .replace(/keep it light\/clean/i, '') // Specific cleanup for known noisy notes
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

// --- 2. OPTIMIZED IMPLEMENTATION ---
// Hoisted Regexes
const REGEX_LEVEL = /(Primary|Secondary|Tertiary)/i;
const REGEX_SCORE = /(\d+)/;
const REGEX_CLEAN_CHARS = /[~>]/g;
const REGEX_CLEAN_PHRASE = /keep it light\/clean/i;

const parseImpact_Optimized = (note) => {
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

// --- 3. TEST DATA & VERIFICATION ---
const testCases = [
    "Primary Chest 95; Secondary Triceps 60",
    "Primary Lats 90; Secondary Biceps 50; Tertiary Rear Delts 20",
    "Primary Quads 95~",
    "Primary ~Chest 90 > keep it light/clean",
    "Nothing to see here",
    "",
    null
];

console.log("--- VERIFICATION ---");
let passed = true;
testCases.forEach((note, idx) => {
    try {
        const res1 = parseImpact_Current(note);
        const res2 = parseImpact_Optimized(note);
        assert.deepStrictEqual(res1, res2);
        // console.log(`Test Case ${idx}: PASSED`);
    } catch (e) {
        console.error(`Test Case ${idx}: FAILED`);
        console.error("Input:", note);
        console.error("Current:", parseImpact_Current(note));
        console.error("Optimized:", parseImpact_Optimized(note));
        passed = false;
    }
});

if (!passed) {
    console.error("Verification failed. Aborting benchmark.");
    process.exit(1);
}
console.log("All verifications passed.\n");

// --- 4. BENCHMARK ---
const ITERATIONS = 100000;
console.log(`--- BENCHMARK (${ITERATIONS} iterations) ---`);

// Warmup
for (let i = 0; i < 1000; i++) {
    testCases.forEach(t => {
        parseImpact_Current(t);
        parseImpact_Optimized(t);
    });
}

// Measure Current
const start1 = performance.now();
for (let i = 0; i < ITERATIONS; i++) {
    testCases.forEach(t => parseImpact_Current(t));
}
const end1 = performance.now();
const time1 = end1 - start1;

// Measure Optimized
const start2 = performance.now();
for (let i = 0; i < ITERATIONS; i++) {
    testCases.forEach(t => parseImpact_Optimized(t));
}
const end2 = performance.now();
const time2 = end2 - start2;

console.log(`Current Implementation:   ${time1.toFixed(2)} ms`);
console.log(`Optimized Implementation: ${time2.toFixed(2)} ms`);

const improvement = ((time1 - time2) / time1) * 100;
console.log(`Improvement:              ${improvement.toFixed(2)}%`);
