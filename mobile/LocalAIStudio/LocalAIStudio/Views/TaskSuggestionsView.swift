import SwiftUI

struct TaskSuggestionsView: View {
    let suggestions: [TaskSuggestion]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Generated Tasks")
                .font(.headline)
                .foregroundColor(.primary)
            
            ForEach(Array(suggestions.enumerated()), id: \.offset) { index, suggestion in
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text(suggestion.title)
                            .font(.subheadline)
                            .fontWeight(.medium)
                        
                        Spacer()
                        
                        Text(suggestion.priority)
                            .font(.caption)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 2)
                            .background(priorityColor(suggestion.priority))
                            .foregroundColor(.white)
                            .cornerRadius(8)
                    }
                    
                    Text(suggestion.description)
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Text(suggestion.category)
                        .font(.caption)
                        .foregroundColor(.blue)
                }
                .padding()
                .background(Color.gray.opacity(0.05))
                .cornerRadius(8)
            }
        }
        .padding()
        .background(Color.blue.opacity(0.05))
        .cornerRadius(12)
    }
    
    private func priorityColor(_ priority: String) -> Color {
        switch priority.lowercased() {
        case "low": return .green
        case "medium": return .orange
        case "high": return .red
        default: return .gray
        }
    }
}

#Preview {
    TaskSuggestionsView(suggestions: [
        TaskSuggestion(
            title: "Learn SwiftUI",
            description: "Study SwiftUI fundamentals and build sample apps",
            category: "Learning", priority: "High"
        ),
        TaskSuggestion(
            title: "Practice Coding",
            description: "Solve coding challenges daily",
            category: "Practice", priority: "Medium"
        )
    ])
}
