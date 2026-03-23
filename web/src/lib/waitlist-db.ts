import { supabase } from './supabase';

export interface Waitlist {
    id: string;
    title: string;
    description: string;
    target_audience: string;
    created_at: string;
    emails: string[];
}

export const WaitlistDB = {
    create: async (title: string, description: string, target_audience: string): Promise<Waitlist | null> => {
        // Rastgele ID üret (örn: idea-a1b2c3d4)
        const id = "idea-" + Math.random().toString(36).substring(2, 10);
        
        const newWaitlist = {
            id,
            title,
            description,
            target_audience,
            emails: []
        };

        const { data, error } = await supabase
            .from('waitlists')
            .insert([newWaitlist])
            .select()
            .single();

        if (error) {
            console.error("Error creating waitlist in Supabase:", error);
            return null;
        }

        return data as Waitlist;
    },

    get: async (id: string): Promise<Waitlist | null> => {
        const { data, error } = await supabase
            .from('waitlists')
            .select('*')
            .eq('id', id)
            .single();

        if (error) {
            if (error.code !== 'PGRST116') { // not found
                console.error("Error fetching waitlist from Supabase:", error);
            }
            return null;
        }
        return data as Waitlist;
    },

    addEmail: async (id: string, email: string): Promise<boolean> => {
        // Get current waitlist to append email (since it's a TEXT[] array)
        const current = await WaitlistDB.get(id);
        if (!current) return false;

        const emails = current.emails || [];
        if (emails.includes(email)) return true; // Already signed up
        
        emails.push(email);

        const { error } = await supabase
            .from('waitlists')
            .update({ emails })
            .eq('id', id);

        if (error) {
            console.error("Error updating waitlist emails in Supabase:", error);
            return false;
        }
        
        return true;
    }
};
