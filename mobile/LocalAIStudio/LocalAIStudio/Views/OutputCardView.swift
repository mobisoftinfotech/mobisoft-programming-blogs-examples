import SwiftUI

struct OutputCardView: View {
    let title: String
    let content: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.headline)
                .foregroundColor(.primary)
            
            Text(content)
                .font(.body)
                .foregroundColor(.secondary)
                .textSelection(.enabled)
        }
        .padding()
        .background(Color.gray.opacity(0.05))
        .cornerRadius(12)
    }
}

#Preview {
    OutputCardView(
        title: "AI Response",
        content: "This is a sample AI response that demonstrates the output card functionality."
    )
}