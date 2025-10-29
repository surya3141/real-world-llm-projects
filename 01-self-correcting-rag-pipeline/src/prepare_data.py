"""
Prepare sample data for testing the RAG pipeline
"""
from pathlib import Path


def create_sample_documents():
    """Create sample documents for testing"""
    
    # Create directories
    sample_dir = Path("data/sample_docs")
    sample_dir.mkdir(parents=True, exist_ok=True)
    
    # Document 1: France and Paris
    doc1 = sample_dir / "france_general.txt"
    doc1.write_text("""
France: A Country Overview

France is a country located in Western Europe, known for its rich history, culture, and contributions to art, science, and philosophy. The capital city of France is Paris, which is also the largest city in the country.

Geography and Population:
France covers an area of approximately 643,801 square kilometers and has a population of about 67 million people. It borders several countries including Belgium, Luxembourg, Germany, Switzerland, Italy, and Spain.

Government:
France is a unitary semi-presidential republic. The President serves as the head of state, while the Prime Minister is the head of government.

Economy:
France has the seventh-largest economy in the world by nominal GDP. Key industries include aerospace, automotive, luxury goods, tourism, and agriculture.
""")

    # Document 2: Paris Details
    doc2 = sample_dir / "paris_city.txt"
    doc2.write_text("""
Paris: The City of Light

Paris is the capital and most populous city of France, with an estimated population of 2.2 million residents within the city proper and over 12 million in the metropolitan area.

History:
Paris has been a major settlement for over two thousand years. The city played a pivotal role in the French Revolution and has been a center of art, fashion, and culture for centuries.

Landmarks and Attractions:
- The Eiffel Tower: Built in 1889, stands 330 meters tall
- The Louvre Museum: World's largest art museum
- Notre-Dame Cathedral: Medieval Catholic cathedral
- Arc de Triomphe: Monument honoring French soldiers
- Champs-Élysées: Famous avenue known for shopping

Culture:
Paris is renowned for its café culture, haute cuisine, and fashion industry. It hosts numerous cultural events and is home to many world-class universities and research institutions.
""")

    # Document 3: Eiffel Tower
    doc3 = sample_dir / "eiffel_tower.txt"
    doc3.write_text("""
The Eiffel Tower: An Engineering Marvel

The Eiffel Tower is a wrought-iron lattice tower located on the Champ de Mars in Paris, France. It is one of the most recognizable structures in the world.

Construction:
- Designed by: Gustave Eiffel's engineering company
- Construction period: 1887-1889
- Purpose: Entrance arch for the 1889 World's Fair
- Height: 330 meters (1,083 feet) including antennas
- Weight: Approximately 10,100 tons
- Material: Wrought iron

Technical Details:
The tower is composed of three levels accessible to the public. Visitors can reach the first and second levels by stairs or elevator, while the third level is only accessible by elevator.

The tower was initially criticized by some of Paris's leading artists and intellectuals, but it has become a global cultural icon of France and one of the most visited paid monuments in the world.

Facts:
- It took 2 years, 2 months, and 5 days to build
- Uses about 20,000 light bulbs for illumination
- Painted every 7 years to prevent rust
- Originally intended to be temporary and demolished after 20 years
- Receives approximately 7 million visitors per year
""")

    # Document 4: French Culture
    doc4 = sample_dir / "french_culture.txt"
    doc4.write_text("""
French Culture and Heritage

French culture is renowned worldwide for its contributions to art, literature, philosophy, and cuisine.

Cuisine:
French cuisine is considered one of the finest in the world. Famous dishes include croissants, baguettes, coq au vin, ratatouille, and crème brûlée. France is also famous for its wine production, with regions like Bordeaux, Burgundy, and Champagne producing world-class wines.

Art and Literature:
France has produced numerous influential artists and writers including:
- Claude Monet (Impressionist painter)
- Victor Hugo (Author of Les Misérables)
- Molière (Playwright)
- Jean-Paul Sartre (Philosopher)

Fashion:
Paris is considered the fashion capital of the world, hosting the prestigious Paris Fashion Week twice a year. French fashion houses like Chanel, Dior, and Louis Vuitton are globally recognized.

Language:
French is a Romance language spoken by approximately 275 million people worldwide. It is an official language in 29 countries and is one of the six official languages of the United Nations.
""")

    # Document 5: Unrelated - Technology
    doc5 = sample_dir / "technology.txt"
    doc5.write_text("""
Modern Technology Trends

Artificial Intelligence:
AI and machine learning are transforming industries worldwide. Applications include natural language processing, computer vision, and predictive analytics.

Cloud Computing:
Cloud services from providers like AWS, Azure, and Google Cloud enable scalable infrastructure and distributed computing capabilities.

Blockchain:
Blockchain technology provides decentralized, secure ledgers for various applications beyond cryptocurrency, including supply chain management and digital identity verification.

Internet of Things (IoT):
IoT devices are connecting everyday objects to the internet, enabling smart homes, smart cities, and industrial automation.
""")

    print(f"✓ Created 5 sample documents in {sample_dir}")
    print("Documents created:")
    for file in sample_dir.glob("*.txt"):
        print(f"  - {file.name}")


if __name__ == "__main__":
    create_sample_documents()
    print("\nSample documents are ready for testing!")
    print("\nNext steps:")
    print("1. Run: python src/main.py --setup")
    print("2. Query: python src/main.py --query 'What is the Eiffel Tower?'")
    print("3. Or launch web interface: streamlit run src/app.py")
