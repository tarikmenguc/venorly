import { supabase } from './supabase';

export interface Alert {
    id: string;
    keyword: string;
    channels: string[];
    frequency: 'daily' | 'weekly' | 'realtime';
    is_active: boolean;
    created_at: string;
}

export const AlertDB = {
    create: async (keyword: string, channels: string[], frequency: string): Promise<Alert | null> => {
        const newAlert = {
            keyword,
            channels: channels || ['reddit', 'github', 'huggingface'],
            frequency: frequency || 'daily',
            is_active: true
        };

        const { data, error } = await supabase
            .from('alerts')
            .insert([newAlert])
            .select()
            .single();

        if (error) {
            console.error("Error creating alert in Supabase:", error);
            return null;
        }

        return data as Alert;
    },

    getAll: async (): Promise<Alert[]> => {
        const { data, error } = await supabase
            .from('alerts')
            .select('*')
            .order('created_at', { ascending: false });

        if (error) {
            console.error("Error fetching all alerts:", error);
            return [];
        }
        return data as Alert[];
    },

    toggleStatus: async (id: string, is_active: boolean): Promise<boolean> => {
        const { error } = await supabase
            .from('alerts')
            .update({ is_active })
            .eq('id', id);

        if (error) {
            console.error("Error toggling alert status:", error);
            return false;
        }
        return true;
    },
    
    delete: async (id: string): Promise<boolean> => {
        const { error } = await supabase
            .from('alerts')
            .delete()
            .eq('id', id);

        if (error) {
            console.error("Error deleting alert:", error);
            return false;
        }
        return true;
    }
};
