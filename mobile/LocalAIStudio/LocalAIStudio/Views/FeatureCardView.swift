import SwiftUI

struct FeatureCardView: View {
    let feature: ContentView.AIFeature
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 8) {
                Image(systemName: feature.icon)
                    .font(.title2)
                    .foregroundColor(isSelected ? .white : .blue)
                
                Text(feature.rawValue)
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(isSelected ? .white : .primary)
                    .multilineTextAlignment(.center)
            }
            .frame(width: 100, height: 80)
            .background(isSelected ? Color.blue : Color.gray.opacity(0.1))
            .cornerRadius(12)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

#Preview {
    FeatureCardView(
        feature: .textGeneration,
        isSelected: true,
        action: {}
    )
}
