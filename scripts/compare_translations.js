
const fs = require('fs');
const vm = require('vm');
const path = require('path');

const targetFile = path.join(__dirname, '../translations.js');
let code = fs.readFileSync(targetFile, 'utf8');
// Append assignment to global
code += '; global.TRANSLATIONS = TRANSLATIONS;';

const sandbox = { global: {} };
vm.createContext(sandbox);
vm.runInContext(code, sandbox);

const en = sandbox.global.TRANSLATIONS.en;
const hr = sandbox.global.TRANSLATIONS.hr;

function getAllKeys(obj, prefix = '') {
    return Object.keys(obj).reduce((res, el) => {
        if(Array.isArray(obj[el])) return res;
        if(typeof obj[el] === 'object' && obj[el] !== null) {
            return [...res, ...getAllKeys(obj[el], prefix + el + '.')];
        }
        return [...res, prefix + el];
    }, []);
}

const enKeys = getAllKeys(en);
const hrKeys = getAllKeys(hr);

const missingInHr = enKeys.filter(k => !hrKeys.includes(k));

console.log('Missing keys in HR:', missingInHr);
