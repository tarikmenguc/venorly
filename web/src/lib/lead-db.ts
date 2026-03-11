import fs from 'fs';
import path from 'path';

const DATA_DIR = path.join(process.cwd(), '.data');
const LEADS_FILE = path.join(DATA_DIR, 'leads.json');

export interface Lead {
    id: string;
    source: string;           // Upwork, Reddit, GitHub, n8n Forum
    title: string;
    url: string;
    desc: string;
    score: number;
    status: 'new' | 'contacted' | 'converted' | 'archived';
    dm_template: string;     // Kişiselleştirilmiş DM şablonu
    scan_category: string;   // Hangi taramadan geldi
    added_at: string;
}

function initDb() {
    if (!fs.existsSync(DATA_DIR)) {
        fs.mkdirSync(DATA_DIR, { recursive: true });
    }
    if (!fs.existsSync(LEADS_FILE)) {
        fs.writeFileSync(LEADS_FILE, JSON.stringify([], null, 2), 'utf-8');
    }
}

function getDb(): Lead[] {
    initDb();
    try {
        const data = fs.readFileSync(LEADS_FILE, 'utf-8');
        return JSON.parse(data);
    } catch {
        return [];
    }
}

function saveDb(leads: Lead[]) {
    initDb();
    fs.writeFileSync(LEADS_FILE, JSON.stringify(leads, null, 2), 'utf-8');
}

export const LeadDB = {
    addMany: (leads: Array<{
        source: string;
        title: string;
        url?: string;
        desc?: string;
        score?: number;
        dm_template?: string;
        scan_category?: string;
    }>): Lead[] => {
        const existing = getDb();
        const newLeads: Lead[] = leads.map(l => ({
            id: 'lead-' + Date.now().toString(36) + Math.random().toString(36).substring(2, 6),
            source: l.source || 'Unknown',
            title: l.title || '',
            url: l.url || '',
            desc: l.desc || '',
            score: l.score || 0,
            status: 'new' as const,
            dm_template: l.dm_template || '',
            scan_category: l.scan_category || '',
            added_at: new Date().toISOString(),
        }));
        existing.unshift(...newLeads);
        saveDb(existing);
        return newLeads;
    },

    getAll: (): Lead[] => getDb(),

    getByStatus: (status: Lead['status']): Lead[] => getDb().filter(l => l.status === status),

    updateStatus: (id: string, status: Lead['status']): boolean => {
        const leads = getDb();
        const lead = leads.find(l => l.id === id);
        if (!lead) return false;
        lead.status = status;
        saveDb(leads);
        return true;
    },

    getStats: () => {
        const leads = getDb();
        return {
            total: leads.length,
            new_count: leads.filter(l => l.status === 'new').length,
            contacted: leads.filter(l => l.status === 'contacted').length,
            converted: leads.filter(l => l.status === 'converted').length,
            archived: leads.filter(l => l.status === 'archived').length,
            by_source: leads.reduce((acc, l) => {
                acc[l.source] = (acc[l.source] || 0) + 1;
                return acc;
            }, {} as Record<string, number>),
        };
    },
};
