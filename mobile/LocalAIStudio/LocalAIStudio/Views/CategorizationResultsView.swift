import SwiftUI

struct CategorizationResultsView: View {
    let results: [String]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Analysis Results")
                .font(.headline)
                .foregroundColor(.primary)
            
            LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 2), spacing: 8) {
                ForEach(results, id: \.self) { result in
                    Text(result)
                        .font(.caption)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 6)
                        .background(Color.purple.opacity(0.1))
                        .foregroundColor(.purple)
                        .cornerRadius(8)
                }
            }
        }
        .padding()
        .background(Color.purple.opacity(0.05))
        .cornerRadius(12)
    }
}

#Preview {
    CategorizationResultsView(results: [
        "Technology",
        "Positive",
        "iPhone",
        "Camera",
        "Battery",
        "Design"
    ])
}
