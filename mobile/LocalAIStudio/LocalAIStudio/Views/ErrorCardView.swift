import SwiftUI

struct ErrorCardView: View {
    let error: String
    
    var body: some View {
        HStack {
            Image(systemName: "exclamationmark.triangle")
                .foregroundColor(.red)
            
            Text(error)
                .font(.caption)
                .foregroundColor(.red)
        }
        .padding()
        .background(Color.red.opacity(0.1))
        .cornerRadius(8)
    }
}

#Preview {
    ErrorCardView(error: "An error occurred while processing your request")
}