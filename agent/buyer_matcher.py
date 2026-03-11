import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.deep_agent import get_llm

class BuyerMatcherAgent:
    """
    Rapor tamamlandıktan sonra çalışır. Fikri satın alacak kişileri
    reality_intel kaynaklarından (Upwork, Reddit, GitHub) toplar ve LLM ile hedefe yönelik DM'ler yazar.
    """
    
    def generate_hyper_personalized_pitch(self, buyer_profile: str, pain_text: str, saas_idea: str, platform: str) -> str:
        """LLM ile kişiselleştirilmiş Upwork teklifi veya Reddit DM'i üretir."""
        
        prompt = f"""
        You are a highly skilled indie hacker/developer. You want to send a cold DM to a potential buyer on {platform}.
        
        Buyer Profile/Source: {buyer_profile}
        Their specific complaint/pain point: {pain_text}
        Your SaaS Idea/Solution: {saas_idea}
        
        Write a short, casual, and highly personalized cold outreach message.
        CRITICAL RULES (Friction Economy):
        1. DO NOT say "Buy my product". Focus purely on the fact that you built a script to save them HOURS of manual work.
        2. Say something like: "Hey, I saw your post about wasting hours on [pain]. I actually built a tiny 1-click script that automates exactly this. Want me to send the link to try it?"
        3. Maximum 3 sentences.
        4. No corporate jargon. Be extremely natural, like one developer talking to a colleague.
        """
        
        llm = get_llm()
        if not llm:
            return "Hi, I built a tool that solves your problem. Check it out!"
            
        try:
            response = llm.invoke(prompt)
            # Response might be a string or AIMessage object depending on langchain version
            content = response.content if hasattr(response, 'content') else str(response)
            return content.strip()
        except Exception as e:
            print(f"[BuyerMatcher] LLM Error: {e}")
            return "Hey! I built a tool that solves exactly this issue. Would you like to try it out?"

    def process_leads(self, raw_leads: list, saas_idea: str) -> list:
        """
        reality_intel'den (Upwork, Reddit) gelen ham listeyi alır ve onlara satış metinlerini ekler.
        """
        matched_leads = []
        for lead in raw_leads:
            pitch = self.generate_hyper_personalized_pitch(
                buyer_profile=lead.get('source', 'Unknown'),
                pain_text=lead.get('desc', lead.get('title', '')),
                saas_idea=saas_idea,
                platform=lead.get('source', 'Web')
            )
            
            lead['sales_pitch'] = pitch
            matched_leads.append(lead)
            
        return matched_leads

if __name__ == "__main__":
    # Test
    matcher = BuyerMatcherAgent()
    mock_lead = {
        "source": "Reddit (r/accounting)",
        "title": "Is there a tool to match invoices?",
        "desc": "I spend 4 hours a day manually matching PDF invoices to stripe payments."
    }
    
    print("Test: Generating Pitch...")
    pitch = matcher.process_leads([mock_lead], "AI Invoice Matcher for Stripe")
    print(f"\nResult:\n{pitch[0]['sales_pitch']}")
