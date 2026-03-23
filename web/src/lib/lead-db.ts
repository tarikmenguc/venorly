import { supabase } from './supabase';

export interface Lead {
    id: string;
    source: string;
    title: string;
    url: string;
    description: string;
    score: number;
    status: 'new' | 'contacted' | 'converted' | 'archived';
    dm_template: string;
    scan_category: string;
    created_at: string;
}

export const LeadDB = {
    addMany: async (leads: Array<{
        source: string;
        title: string;
        url?: string;
        description?: string;
        score?: number;
        dm_template?: string;
        scan_category?: string;
    }>): Promise<Lead[]> => {
        const newLeads = leads.map(l => ({
            source: l.source || 'Unknown',
            title: l.title || '',
            url: l.url || '',
            description: l.description || '',
            score: l.score || 0,
            status: 'new',
            dm_template: l.dm_template || '',
            scan_category: l.scan_category || ''
        }));

        const { data, error } = await supabase
            .from('leads')
            .insert(newLeads)
            .select();

        if (error) {
            console.error("Error inserting leads deeply:", error);
            return [];
        }
        return data as Lead[];
    },

    getAll: async (): Promise<Lead[]> => {
        const { data, error } = await supabase
            .from('leads')
            .select('*')
            .order('created_at', { ascending: false });

        if (error) {
            console.error("Error fetching leads:", error);
            return [];
        }
        return data as Lead[];
    },

    getByStatus: async (status: Lead['status']): Promise<Lead[]> => {
        const { data, error } = await supabase
            .from('leads')
            .select('*')
            .eq('status', status)
            .order('created_at', { ascending: false });

        if (error) {
            console.error(`Error fetching leads by status ${status}:`, error);
            return [];
        }
        return data as Lead[];
    },

    updateStatus: async (id: string, status: Lead['status']): Promise<boolean> => {
        const { error } = await supabase
            .from('leads')
            .update({ status })
            .eq('id', id);

        if (error) {
            console.error("Error updating lead status:", error);
            return false;
        }
        return true;
    },

    getStats: async () => {
        const { data: leads, error } = await supabase
            .from('leads')
            .select('status, source');

        if (error || !leads) {
            return {
                total: 0, new_count: 0, contacted: 0, converted: 0, archived: 0, by_source: {}
            };
        }

        return {
            total: leads.length,
            new_count: leads.filter(l => l.status === 'new').length,
            contacted: leads.filter(l => l.status === 'contacted').length,
            converted: leads.filter(l => l.status === 'converted').length,
            archived: leads.filter(l => l.status === 'archived').length,
            by_source: leads.reduce((acc, l) => {
                const src = l.source as string;
                acc[src] = (acc[src] || 0) + 1;
                return acc;
            }, {} as Record<string, number>),
        };
    },
};
