import schedule
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from .live_scraper import JobListingScraper
import os
from .telegram_exporter import TelegramExporter
import google.generativeai as genai

def list_gemini_models():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print('[Gemini] No API key set.')
        return
    try:
        genai.configure(api_key=api_key)
        print('[Gemini] Available models:')
        for model in genai.list_models():
            print(f"- {model.name}")
    except Exception as e:
        print(f"[Gemini] Error listing models: {e}")

class JobScheduler:
    def __init__(self):
        self.scraper = JobListingScraper()
        self.last_run_time = None
        self.keywords = [
            "Frontend Developer", "UI/UX Designer", "Machine Learning", "Product Intern",
            "Software Engineer", "AI", "Research Intern", "Design Intern"
        ]
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, '..', 'data')
        os.makedirs(data_dir, exist_ok=True)
        self.active_jobs = []
        self.job_file = os.path.join(data_dir, "active_jobs.json")
        self._load_jobs()
        self.telegram_exporter = TelegramExporter()

    def _load_jobs(self):
        if os.path.exists(self.job_file):
            with open(self.job_file, 'r') as f:
                self.active_jobs = json.load(f)
        else:
            self.active_jobs = []

    def _save_jobs(self):
        with open(self.job_file, 'w') as f:
            json.dump(self.active_jobs, f, indent=2)

    def run_job_hunt(self):
        print(f"🕐 Running job hunt at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        since_time = self.last_run_time or (datetime.now() - timedelta(hours=4))
        print("[DEBUG] Fetching from all sources...")
        new_listings = self.scraper.fetch_all(self.keywords, since_time)
        print(f"[DEBUG] Total listings fetched: {len(new_listings)}")
        for src in ['LinkedIn', 'Unstop', 'Internshala', 'Cuvette', 'Wellfound']:
            count = sum(1 for l in new_listings if l.get('source') == src)
            print(f"[DEBUG] {src}: {count} listings fetched")
        # Filter out irrelevant domains (e.g., mechanical, civil, non-tech)
        relevant_domains = [
            'software', 'developer', 'design', 'ui', 'ux', 'machine learning', 'ai', 'product', 'research', 'frontend', 'backend', 'intern', 'engineer', 'data', 'python', 'javascript', 'web', 'app', 'cloud', 'fullstack', 'ml', 'dl', 'artificial intelligence', 'computer', 'technology', 'tech', 'product manager', 'product design', 'case competition', 'hackathon', 'sprint'
        ]
        def is_relevant(listing):
            text = (listing.get('title', '') + ' ' + ' '.join(listing.get('tags', []))).lower()
            return any(domain in text for domain in relevant_domains)
        filtered = [l for l in new_listings if is_relevant(l)]
        # Deduplicate by (title, company, posted_time)
        seen = set()
        deduped = []
        for l in filtered:
            key = (l.get('title', '').strip().lower(), l.get('company', '').strip().lower(), l.get('posted_time', '').strip())
            if key not in seen:
                seen.add(key)
                deduped.append(l)
        # Only keep listings newer than last run (DISABLED: now include all open applications)
        # if self.last_run_time:
        #     def is_new(l):
        #         pt = l.get('posted_time', '')
        #         if not pt:
        #             return True  # If no posted_time, keep
        #         try:
        #             from dateutil import parser
        #             posted_dt = parser.parse(pt)
        #             return posted_dt > self.last_run_time
        #         except:
        #             return True
        #     deduped = [l for l in deduped if is_new(l)]
        # Only filter out jobs/internships with a deadline in the past (if available)
        from dateutil import parser
        filtered_open = []
        filtered_closed = []
        for l in deduped:
            deadline = l.get('deadline', '')
            if deadline:
                try:
                    deadline_dt = parser.parse(deadline)
                    if deadline_dt < datetime.now():
                        filtered_closed.append(l)
                        continue
                except Exception as e:
                    print(f"[DEBUG] Could not parse deadline '{deadline}': {e}")
            filtered_open.append(l)
        print(f"[DEBUG] {len(filtered_closed)} listings filtered out due to past deadline.")
        deduped = filtered_open
        # Separate hackathons/competitions and jobs/internships
        hackathon_tags = {'hackathon', 'case competition', 'sprint', 'competition'}
        hackathons = []
        jobs = []
        for l in deduped:
            tags = set([t.lower() for t in l.get('tags', [])])
            if tags & hackathon_tags:
                hackathons.append(l)
            else:
                jobs.append(l)
        # Sort hackathons by soonest deadline (if available)
        from dateutil import parser
        def deadline_key(l):
            try:
                return parser.parse(l.get('deadline', '2099-12-31'))
            except:
                return parser.parse('2099-12-31')
        hackathons.sort(key=deadline_key)
        # Sort jobs by most recent posted_time (if available)
        def posted_key(l):
            try:
                return -parser.parse(l.get('posted_time', '1970-01-01')).timestamp()
            except:
                return 0
        jobs.sort(key=posted_key)
        # Send only the top 5 hackathons (Unstop) and top 5 jobs/internships
        top_hackathons = [h for h in hackathons if h.get('source') == 'Unstop'][:5]
        top_jobs = jobs[:5]
        for h in top_hackathons:
            msg = self._generate_gemini_message(h, is_hackathon=True) or self._format_job_message(h, is_hackathon=True)
            self.telegram_exporter._send_message(msg)
        for job in top_jobs:
            msg = self._generate_gemini_message(job, is_hackathon=False) or self._format_job_message(job, is_hackathon=False)
            self.telegram_exporter._send_message(msg)
        self.active_jobs.extend(deduped)
        self._save_jobs()
        print(f"✅ Job hunt complete! {len(deduped)} new relevant jobs found.")
        for job in deduped[:10]:
            print(f"- {job['title']} at {job['company']} ({job['source']}) | {job['link']}")
        if len(deduped) > 10:
            print(f"...and {len(deduped)-10} more.")
        self.last_run_time = datetime.now()

    def _format_job_message(self, job, is_hackathon=False):
        msg = ""
        if is_hackathon:
            msg += "🏆 *Hackathon/Competition*\n"
            if any(t in (job.get('tags') or []) for t in ['hackathon', 'case competition', 'sprint']):
                msg += "🔥 *High Demand!*\n"
        else:
            msg += "💼 *Job/Internship*\n"
        if job.get('title'):
            msg += f"*{job.get('title')}*\n"
        if job.get('company'):
            msg += f"🏢 *Company:* {job.get('company')}\n"
        if job.get('location'):
            msg += f"📍 *Location:* {job.get('location')}\n"
        if job.get('work_type'):
            msg += f"🏷️ *Work Type:* {job.get('work_type')}\n"
        if job.get('posted_time'):
            msg += f"🕒 *Posted:* {job.get('posted_time')}\n"
        if job.get('deadline'):
            msg += f"⏰ *Deadline:* {job.get('deadline')}\n"
        if job.get('team_size'):
            msg += f"👥 *Team Size:* {job.get('team_size')}\n"
        if job.get('eligibility'):
            msg += f"🎓 *Eligibility:* {job.get('eligibility')}\n"
        if job.get('tags'):
            msg += f"🏷️ *Tags:* {', '.join(job.get('tags'))}\n"
        if job.get('link'):
            msg += f"🔗 [Apply/Register Here]({job.get('link')})\n"
        msg += f"🌐 *Source:* {job.get('source', '')}"
        return msg

    def _generate_gemini_message(self, job, is_hackathon=False):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('models/gemini-pro')
            prompt = "Write a concise, engaging Telegram message for this "
            prompt += "hackathon/competition" if is_hackathon else "job/internship"
            prompt += ":\n" + str(job)
            response = model.generate_content(prompt)
            print(f"[Gemini] Success: Message generated.")
            return response.text.strip() if hasattr(response, 'text') else str(response)
        except Exception as e:
            print(f"[Gemini] Error: {e}")
            return None

    def start_scheduler(self):
        print("🚀 Starting Job MCP Scheduler...")
        print("⏰ Will run every 3 hours")
        schedule.every(3).hours.do(self.run_job_hunt)
        self.run_job_hunt()
        while True:
            schedule.run_pending()
            time.sleep(60)

if __name__ == "__main__":
    print("[job_hawk] Running job/internship/competition tracker...")
    list_gemini_models()
    scheduler = JobScheduler()
    scheduler.run_job_hunt() 