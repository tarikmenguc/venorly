import fs from 'fs';
import path from 'path';

const DATA_DIR = path.join(process.cwd(), '.data');
const SCANS_FILE = path.join(DATA_DIR, 'scans.json');

export interface ScanRecord {
    id: string;
    category: string;
    mode: string;       // discover, deep, orchestrate, reverse, trends
    created_at: string;
    status: 'running' | 'completed' | 'failed';
    report_preview: string; // ilk 200 karakter
    leads_count: number;
    angles_count: number;
}

function initDb() {
    if (!fs.existsSync(DATA_DIR)) {
        fs.mkdirSync(DATA_DIR, { recursive: true });
    }
    if (!fs.existsSync(SCANS_FILE)) {
        fs.writeFileSync(SCANS_FILE, JSON.stringify([], null, 2), 'utf-8');
    }
}

function getDb(): ScanRecord[] {
    initDb();
    try {
        const data = fs.readFileSync(SCANS_FILE, 'utf-8');
        return JSON.parse(data);
    } catch {
        return [];
    }
}

function saveDb(records: ScanRecord[]) {
    initDb();
    fs.writeFileSync(SCANS_FILE, JSON.stringify(records, null, 2), 'utf-8');
}

export const ScanDB = {
    create: (category: string, mode: string): ScanRecord => {
        const records = getDb();
        const scan: ScanRecord = {
            id: 'scan-' + Date.now().toString(36) + Math.random().toString(36).substring(2, 6),
            category,
            mode,
            created_at: new Date().toISOString(),
            status: 'running',
            report_preview: '',
            leads_count: 0,
            angles_count: 0,
        };
        records.unshift(scan); // En yeni en başta
        saveDb(records);
        return scan;
    },

    complete: (id: string, report_preview: string, leads_count: number, angles_count: number) => {
        const records = getDb();
        const scan = records.find(r => r.id === id);
        if (scan) {
            scan.status = 'completed';
            scan.report_preview = report_preview.substring(0, 200);
            scan.leads_count = leads_count;
            scan.angles_count = angles_count;
            saveDb(records);
        }
    },

    fail: (id: string) => {
        const records = getDb();
        const scan = records.find(r => r.id === id);
        if (scan) {
            scan.status = 'failed';
            saveDb(records);
        }
    },

    getAll: (): ScanRecord[] => getDb(),

    getRecent: (limit: number = 10): ScanRecord[] => getDb().slice(0, limit),

    getStats: () => {
        const records = getDb();
        return {
            total_scans: records.length,
            completed: records.filter(r => r.status === 'completed').length,
            total_leads: records.reduce((sum, r) => sum + r.leads_count, 0),
            total_angles: records.reduce((sum, r) => sum + r.angles_count, 0),
            modes: {
                discover: records.filter(r => r.mode === 'discover').length,
                deep: records.filter(r => r.mode === 'deep').length,
                orchestrate: records.filter(r => r.mode === 'orchestrate').length,
                reverse: records.filter(r => r.mode === 'reverse').length,
                trends: records.filter(r => r.mode === 'trends').length,
            },
        };
    },
};
