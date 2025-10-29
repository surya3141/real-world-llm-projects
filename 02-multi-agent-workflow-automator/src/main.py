"""
Command-line interface for Multi-Agent Workflow Automator
"""
import argparse
from workflow_automator import MarketingCampaignCrew
from dotenv import load_dotenv

load_dotenv()


def create_campaign(args):
    """Create a marketing campaign"""
    print("="*70)
    print("Multi-Agent Marketing Campaign Creator")
    print("="*70)
    print(f"\nProduct: {args.product}")
    print(f"Audience: {args.audience}")
    if args.goal:
        print(f"Goal: {args.goal}")
    print("\n" + "="*70)
    print("Agents are collaborating...")
    print("="*70 + "\n")
    
    crew = MarketingCampaignCrew()
    
    result = crew.create_campaign(
        product=args.product,
        audience=args.audience,
        campaign_goal=args.goal
    )
    
    print("\n" + "="*70)
    print("CAMPAIGN BRIEF")
    print("="*70)
    print(result["campaign_brief"])
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(result["campaign_brief"])
        print(f"\n✓ Campaign saved to: {args.output}")


def interactive_mode():
    """Interactive campaign creation"""
    print("="*70)
    print("Multi-Agent Campaign Creator - Interactive Mode")
    print("="*70)
    
    print("\nLet's create a marketing campaign!\n")
    
    product = input("📦 Product/Service: ").strip()
    if not product:
        print("Error: Product is required")
        return
    
    audience = input("🎯 Target Audience: ").strip()
    if not audience:
        print("Error: Target audience is required")
        return
    
    goal = input("🎪 Campaign Goal (optional): ").strip()
    
    print("\n" + "="*70)
    print("Creating campaign...")
    print("="*70 + "\n")
    
    crew = MarketingCampaignCrew()
    
    result = crew.create_campaign(
        product=product,
        audience=audience,
        campaign_goal=goal if goal else None
    )
    
    print("\n" + "="*70)
    print("CAMPAIGN BRIEF")
    print("="*70)
    print(result["campaign_brief"])
    
    # Ask to save
    save = input("\n💾 Save to file? (y/n): ").strip().lower()
    if save == 'y':
        filename = input("Filename (campaign_brief.txt): ").strip()
        if not filename:
            filename = "campaign_brief.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(result["campaign_brief"])
        print(f"✓ Saved to: {filename}")


def main():
    parser = argparse.ArgumentParser(
        description="Multi-Agent Marketing Campaign Creator CLI"
    )
    
    # Modes
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Start interactive mode"
    )
    
    # Campaign details
    parser.add_argument(
        "--product", "-p",
        type=str,
        help="Product or service to market"
    )
    
    parser.add_argument(
        "--audience", "-a",
        type=str,
        help="Target audience description"
    )
    
    parser.add_argument(
        "--goal", "-g",
        type=str,
        help="Campaign goal (optional)"
    )
    
    # Output
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Save campaign to file"
    )
    
    args = parser.parse_args()
    
    # Execute mode
    if args.interactive:
        interactive_mode()
    elif args.product and args.audience:
        create_campaign(args)
    else:
        parser.print_help()
        print("\nExamples:")
        print('  Interactive: python src/main.py --interactive')
        print('  Direct:      python src/main.py -p "Eco Water Bottle" -a "Millennials" -o brief.txt')


if __name__ == "__main__":
    main()
