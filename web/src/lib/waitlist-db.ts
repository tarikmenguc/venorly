import fs from 'fs';
import path from 'path';

// Local veri saklayacağımız klasör: web/.data
const DATA_DIR = path.join(process.cwd(), '.data');
const DB_FILE = path.join(DATA_DIR, 'waitlists.json');

// Types
export interface Waitlist {
    id: string;
    title: string;
    description: string;
    target_audience: string;
    created_at: string;
    emails: string[];
}

// Ensure db exists
function initDb() {
    if (!fs.existsSync(DATA_DIR)) {
        fs.mkdirSync(DATA_DIR, { recursive: true });
    }
    if (!fs.existsSync(DB_FILE)) {
        fs.writeFileSync(DB_FILE, JSON.stringify({}, null, 2), 'utf-8');
    }
}

// Get all waitlists map
function getDb(): Record<string, Waitlist> {
    initDb();
    const data = fs.readFileSync(DB_FILE, 'utf-8');
    return JSON.parse(data);
}

// Save all 
function saveDb(db: Record<string, Waitlist>) {
    fs.writeFileSync(DB_FILE, JSON.stringify(db, null, 2), 'utf-8');
}

export const WaitlistDB = {
    create: (title: string, description: string, target_audience: string): Waitlist => {
        const db = getDb();
        // Rastgele ID üret (örn: idea-a1b2c3d4)
        const id = "idea-" + Math.random().toString(36).substring(2, 10);

        const newWaitlist: Waitlist = {
            id,
            title,
            description,
            target_audience,
            created_at: new Date().toISOString(),
            emails: []
        };

        db[id] = newWaitlist;
        saveDb(db);
        return newWaitlist;
    },

    get: (id: string): Waitlist | null => {
        const db = getDb();
        return db[id] || null;
    },

    addEmail: (id: string, email: string) => {
        const db = getDb();
        if (!db[id]) return false;

        if (!db[id].emails.includes(email)) {
            db[id].emails.push(email);
            saveDb(db);
        }
        return true;
    }
};
