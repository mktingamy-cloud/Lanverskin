import os
import sys

def print_banner():
    print("=" * 60)
    print("      PIXELPULSE APPAREL — CONTENT ENGINE MVP ORCHESTRATOR")
    print("=" * 60)

def main():
    print_banner()
    
    # Check if there is an action arg
    action = sys.argv[1] if len(sys.argv) > 1 else "run"
    
    if action == "run":
        print("\n[STEP 1] Running Trend Monitor & Draft Generator...")
        from monitor import scan_for_trends
        from generator import generate_and_save_from_trends
        
        trends = scan_for_trends()
        if not trends:
            print("No matching trending topics found on Hacker News or Dev.to today.")
            return
            
        print(f"\nFound {len(trends)} matched trends. Generating up to 2 drafts...")
        generate_and_save_from_trends(trends, max_drafts=2)
        
        print("\n" + "-" * 50)
        print("NEXT STEPS FOR REVIEW & APPROVAL:")
        print("1. Go to the shared team review queue at:")
        print("   /home/team/shared/content_engine/review_queue/")
        print("2. Open the newly generated draft .md file(s).")
        print("3. Review the content. When ready to publish, edit the file and change:")
        print("   <!-- Approved: False -->  ==>  <!-- Approved: True -->")
        print("4. Run the publisher using:")
        print("   python3 ~/Lanverskin/content_engine/run_engine.py publish")
        print("-" * 50)
        
    elif action == "publish":
        print("\n[STEP 2] Running Publisher for Approved Drafts...")
        from publish import publish_approved_articles
        publish_approved_articles()
        
    else:
        print(f"Unknown action: {action}. Use 'run' or 'publish'.")

if __name__ == "__main__":
    main()
