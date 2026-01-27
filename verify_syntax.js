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
