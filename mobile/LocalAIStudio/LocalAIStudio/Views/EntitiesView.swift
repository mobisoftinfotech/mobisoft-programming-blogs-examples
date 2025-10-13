import SwiftUI

struct EntitiesView: View {
    let entities: ExtractedEntities
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Extracted Entities")
                .font(.headline)
                .foregroundColor(.primary)
            
            EntitySection(title: "People", items: entities.people, icon: "person.circle")
            EntitySection(title: "Places", items: entities.places, icon: "location.circle")
            EntitySection(title: "Organizations", items: entities.organizations, icon: "building.2.circle")
            EntitySection(title: "Events", items: entities.events, icon: "calendar.circle")
        }
        .padding()
        .background(Color.green.opacity(0.05))
        .cornerRadius(12)
    }
}

struct EntitySection: View {
    let title: String
    let items: [String]
    let icon: String
    
    var body: some View {
        if !items.isEmpty {
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Image(systemName: icon)
                        .foregroundColor(.blue)
                    Text(title)
                        .font(.subheadline)
                        .fontWeight(.medium)
                }
                
                LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 2), spacing: 4) {
                    ForEach(items, id: \.self) { item in
                        Text(item)
                            .font(.caption)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 2)
                            .background(Color.blue.opacity(0.1))
                            .cornerRadius(4)
                    }
                }
            }
        }
    }
}

#Preview {
    EntitiesView(entities: ExtractedEntities(
        people: ["Steve Jobs", "Tim Cook"],
        places: ["Cupertino", "California"],
        organizations: ["Apple Inc.", "Apple Store"],
        events: ["WWDC 2024", "iPhone Launch"]
    ))
}
