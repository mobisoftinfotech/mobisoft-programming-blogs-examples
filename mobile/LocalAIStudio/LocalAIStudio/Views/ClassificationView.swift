import SwiftUI

struct ClassificationView: View {
    let classification: ContentClassification
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Content Analysis")
                .font(.headline)
                .foregroundColor(.primary)
            
            HStack {
                VStack(alignment: .leading) {
                    Text("Category")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text(classification.category)
                        .font(.subheadline)
                        .fontWeight(.medium)
                }
                
                Spacer()
                
                VStack(alignment: .trailing) {
                    Text("Sentiment")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text(classification.sentiment)
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .foregroundColor(sentimentColor(classification.sentiment))
                }
            }
            
            VStack(alignment: .leading, spacing: 4) {
                Text("Topics")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 3), spacing: 4) {
                    ForEach(classification.topics, id: \.self) { topic in
                        Text(topic)
                            .font(.caption)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(Color.purple.opacity(0.1))
                            .cornerRadius(4)
                    }
                }
            }
            
            HStack {
                Text("Confidence")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Spacer()
                
                Text("\(Int(classification.confidence * 100))%")
                    .font(.caption)
                    .fontWeight(.medium)
            }
        }
        .padding()
        .background(Color.purple.opacity(0.05))
        .cornerRadius(12)
    }
    
    private func sentimentColor(_ sentiment: String) -> Color {
        switch sentiment.lowercased() {
        case "positive": return .green
        case "negative": return .red
        case "neutral": return .gray
        default: return .gray
        }
    }
}

#Preview {
    ClassificationView(classification: ContentClassification(
        category: "Technology",
        sentiment: "Positive",
        topics: ["iPhone", "Camera", "Battery", "Design"],
        confidence: 0.85
    ))
}
