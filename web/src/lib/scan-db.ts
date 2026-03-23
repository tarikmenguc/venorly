import { supabase } from './supabase';

export interface ScanRecord {
    id: string;
    category: string;
    mode: string;
    created_at: string;
    status: 'running' | 'completed' | 'failed';
    report_preview: string;
    leads_count: number;
    angles_count: number;
}

export const ScanDB = {
    create: async (category: string, mode: string): Promise<ScanRecord | null> => {
        const newScan = {
            category,
            mode,
            status: 'running',
            report_preview: '',
            leads_count: 0,
            angles_count: 0,
        };

        const { data, error } = await supabase
            .from('scans')
            .insert([newScan])
            .select()
            .single();

        if (error) {
            console.error("Error creating scan in Supabase:", error);
            return null;
        }

        return data as ScanRecord;
    },

    complete: async (id: string, report_preview: string, leads_count: number, angles_count: number): Promise<void> => {
        const { error } = await supabase
            .from('scans')
            .update({
                status: 'completed',
                report_preview: report_preview.substring(0, 200),
                leads_count,
                angles_count
            })
            .eq('id', id);

        if (error) console.error("Error completing scan in Supabase:", error);
    },

    fail: async (id: string): Promise<void> => {
        const { error } = await supabase
            .from('scans')
            .update({ status: 'failed' })
            .eq('id', id);

        if (error) console.error("Error failing scan in Supabase:", error);
    },

    getById: async (id: string): Promise<ScanRecord | null> => {
        const { data, error } = await supabase
            .from('scans')
            .select('*')
            .eq('id', id)
            .single();

        if (error) {
            console.error("Error fetching scan by ID:", error);
            return null;
        }
        return data as ScanRecord;
    },

    getAll: async (): Promise<ScanRecord[]> => {
        const { data, error } = await supabase
            .from('scans')
            .select('*')
            .order('created_at', { ascending: false });

        if (error) {
            console.error("Error fetching all scans:", error);
            return [];
        }
        return data as ScanRecord[];
    },

    getRecent: async (limit: number = 10): Promise<ScanRecord[]> => {
        const { data, error } = await supabase
            .from('scans')
            .select('*')
            .order('created_at', { ascending: false })
            .limit(limit);

        if (error) {
            console.error("Error fetching recent scans:", error);
            return [];
        }
        return data as ScanRecord[];
    },

    getStats: async () => {
        const { data: records, error } = await supabase
            .from('scans')
            .select('*');

        if (error || !records) {
            return {
                total_scans: 0, completed: 0, total_leads: 0, total_angles: 0,
                modes: { discover: 0, deep: 0, orchestrate: 0, reverse: 0, trends: 0 }
            };
        }

        return {
            total_scans: records.length,
            completed: records.filter(r => r.status === 'completed').length,
            total_leads: records.reduce((sum, r) => sum + (r.leads_count || 0), 0),
            total_angles: records.reduce((sum, r) => sum + (r.angles_count || 0), 0),
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
