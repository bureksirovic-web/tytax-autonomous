// Mock environment
const window = {};

// Mock normalizeMuscleName (Simplified for test)
const normalizeMuscleName = (() => {
    const cache = new Map();
    return (name) => {
        if (!name) return 'Other';
        if (cache.has(name)) return cache.get(name);
        const result = name.charAt(0).toUpperCase() + name.slice(1).toLowerCase();
        cache.set(name, result);
        return result;
    };
})();

// Mock parseImpact dependencies
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

// --- INSERTED CODE FROM INDEX.HTML ---
const getImpact = (() => {
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
// --- END INSERTED CODE ---

// TESTS
let testsPassed = 0;
let testsFailed = 0;

function assert(condition, message) {
    if (condition) {
        console.log(`PASS: ${message}`);
        testsPassed++;
    } else {
        console.error(`FAIL: ${message}`);
        testsFailed++;
    }
}

console.log("--- Starting Verification ---");

// Test 1: V2 Array Format
const exV2 = {
    impact: [
        { m: 'Chest', s: 95 },
        { m: 'Triceps', s: 60 }
    ]
};
const resV2 = getImpact(exV2);
assert(resV2.length === 2, "V2 Array parsed correct length");
assert(resV2[0].muscle === 'Chest' && resV2[0].score === 95, "V2 Item 1 correct");
assert(resV2[0].level === 'Primary', "V2 Level calculation correct");

// Test 2: V3 Object Format
const exV3 = {
    impact: {
        'Lats': 95,
        'Biceps': 40
    }
};
const resV3 = getImpact(exV3);
assert(resV3.length === 2, "V3 Object parsed correct length");
assert(resV3.find(i => i.muscle === 'Lats').score === 95, "V3 Item 1 correct");

// Test 3: Legacy Note Format
const exLegacy = {
    note: "Primary 90 Chest; Secondary 50 Triceps"
};
const resLegacy = getImpact(exLegacy);
assert(resLegacy.length === 2, "Legacy Note parsed correct length");
assert(resLegacy.find(i => i.muscle === 'chest').score === 90, "Legacy Item 1 correct"); // Legacy parser returns lowercase muscle

// Test 4: Caching Identity
const call1 = getImpact(exV2);
const call2 = getImpact(exV2);
assert(call1 === call2, "Cache returns identical object reference");

// Test 5: Cache Miss on New Object
const exV2Copy = { ...exV2 }; // New reference
const call3 = getImpact(exV2Copy);
assert(call1 !== call3, "New object reference generates new result");
assert(call3[0].score === 95, "New result is correct");

console.log(`\nTests Completed: ${testsPassed} Passed, ${testsFailed} Failed.`);
if (testsFailed > 0) process.exit(1);
