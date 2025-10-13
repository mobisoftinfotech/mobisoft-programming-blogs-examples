import SwiftUI
import FoundationModels

@available(iOS 26.0, *)
struct ContentView: View {
    @StateObject private var aiManager = LocalAIManager()
    @State private var inputText = ""
    
    // Working examples for each feature
    private var workingExamples: [AIFeature: String] {
        [
            .textGeneration: textGenerationSamplePrompts.values.randomElement() ?? "Explain how photosynthesis works in plants",
            .summarization: summarizationExamples.values.randomElement() ?? "Apple Inc. was founded in 1976 by Steve Jobs, Steve Wozniak, and Ronald Wayne. The company revolutionized personal computing with products like the Apple II, Macintosh, and later the iPhone. Today, Apple is one of the world's most valuable companies, known for innovation in hardware, software, and services.",
        .taskSuggestions: "I want to learn iOS development",
        .entityExtraction: "Apple Inc. was founded by Steve Jobs in Cupertino, California in 1976",
        .contentClassification: "I love using my new iPhone. The camera quality is amazing and the battery life is excellent.",
        .categorization: "I love using my new iPhone. The camera quality is amazing and the battery life is excellent. The design is sleek and modern. I would definitely recommend this to anyone looking for a premium smartphone.",
        .creativeContent: "Create educational content about the solar system",
        .translation: translationExamples.randomElement() ?? "Good morning! How are you feeling today? I hope you have a wonderful day ahead."
        ]
    }
    
    
    private let textGenerationSamplePrompts = [
        "Story": "Write a story about a mysterious door",
        "Workout": "Create a 30-minute workout routine",
        "Journal": "Give me journal prompts for reflection",
        "Custom": ""
    ]
    
    private let summarizationExamples = [
        "Long Text": "Apple Inc. was founded in 1976 by Steve Jobs, Steve Wozniak, and Ronald Wayne. The company revolutionized personal computing with products like the Apple II, Macintosh, and later the iPhone. Today, Apple is one of the world's most valuable companies, known for innovation in hardware, software, and services. The company has expanded into various markets including smartphones, tablets, computers, wearables, and digital services. Apple's ecosystem approach, where all devices work seamlessly together, has been a key factor in its success. The company continues to focus on privacy, sustainability, and user experience in all its products.",
        "Article": "The rapid advancement of artificial intelligence has transformed numerous industries, from healthcare and finance to transportation and entertainment. Machine learning algorithms can now process vast amounts of data to identify patterns and make predictions with remarkable accuracy. In healthcare, AI is being used to diagnose diseases, develop new treatments, and personalize patient care. Financial institutions leverage AI for fraud detection, algorithmic trading, and risk assessment. The automotive industry is developing autonomous vehicles that could revolutionize transportation. However, these advances also raise important questions about job displacement, privacy, and the need for ethical guidelines in AI development.",
        "Meeting Notes": "The quarterly planning meeting covered several key topics. First, we discussed the Q3 performance metrics, which showed a 15% increase in user engagement and a 8% growth in revenue. The marketing team presented their new campaign strategy focusing on social media and influencer partnerships. The product team shared updates on the mobile app redesign, which is scheduled for release in early Q4. We also reviewed the budget allocation for the next quarter, with increased investment in customer support and infrastructure. Action items include finalizing the marketing budget by next week and completing user testing for the mobile app by month-end."
    ]
    
    private let translationExamples = [
        "Good morning! How are you feeling today? I hope you have a wonderful day ahead.",
        "I would like to order a coffee and a sandwich, please.",
        "Can you help me find the nearest train station?",
        "Thank you very much for your assistance. I really appreciate it.",
        "What time does the museum open on weekends?",
        "I'm learning a new language and it's very exciting!"
    ]
    
    
    
    @State private var outputText = ""
    @State private var selectedFeature: AIFeature = .textGeneration
    @State private var taskSuggestions: [TaskSuggestion] = []
    @State private var extractedEntities: ExtractedEntities?
    @State private var contentClassification: ContentClassification?
    @State private var categorizationResults: [String] = []
    @State private var selectedCreativeType: CreativeType = .story
    @State private var targetLanguage = "Spanish"
    @State private var detectedLanguage = "en"
    
    enum AIFeature: String, CaseIterable {
        case textGeneration = "Text Generation"
        case summarization = "Summarization"
        case taskSuggestions = "Task Suggestions"
        case entityExtraction = "Entity Extraction"
        case contentClassification = "Content Classification"
        case categorization = "Content Categorization"
        case creativeContent = "Creative Content"
        case translation = "Translation"
        
        var description: String {
            switch self {
            case .textGeneration:
                return "Generate text using Apple's on-device AI model"
            case .summarization:
                return "Summarize long texts concisely"
            case .taskSuggestions:
                return "Generate structured task suggestions"
            case .entityExtraction:
                return "Extract people, places, organizations from text"
            case .contentClassification:
                return "Classify content by category and sentiment"
            case .categorization:
                return "Analyze and categorize text content with detailed examples"
            case .creativeContent:
                return "Generate stories, poems, and creative content"
            case .translation:
                return "Translate text between different languages"
            }
        }
        
        var icon: String {
            switch self {
            case .textGeneration: return "text.bubble"
            case .summarization: return "doc.text"
            case .taskSuggestions: return "checklist"
            case .entityExtraction: return "magnifyingglass.circle"
            case .contentClassification: return "tag.circle"
            case .categorization: return "tag.circle.fill"
            case .creativeContent: return "paintbrush"
            case .translation: return "globe"
            }
        }
    }
    
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Image(systemName: "brain.head.profile")
                            .font(.title2)
                            .foregroundColor(.blue)
                        
                        Text("Apple Intelligence Demo")
                            .font(.title2)
                            .fontWeight(.bold)
                        
                        Spacer()
                        HStack(spacing: 4) {
                            Circle()
                                .fill(aiManager.isFoundationModelAvailable ? .green : .red)
                                .frame(width: 8, height: 8)
                            Text(aiManager.isFoundationModelAvailable ? "Available" : "Unavailable")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                    
                    Text("Real on-device AI using Apple's Foundation Models framework")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(.horizontal)
                
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 12) {
                        ForEach(AIFeature.allCases, id: \.self) { feature in
                            FeatureCardView(
                                feature: feature,
                                isSelected: selectedFeature == feature
                            ) {
                                selectedFeature = feature
                                outputText = ""
                                taskSuggestions = []
                                extractedEntities = nil
                                contentClassification = nil
                                categorizationResults = []
                                
                                // Detect language when switching to translation
                                if feature == .translation {
                                    detectedLanguage = aiManager.detectLanguage(inputText)
                                }
                            }
                        }
                    }
                    .padding(.horizontal)
                }
                
                // Input Section
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Image(systemName: selectedFeature.icon)
                            .foregroundColor(.blue)
                        Text(selectedFeature.rawValue)
                            .font(.headline)
                        Spacer()
                    }
                    
                    Text(selectedFeature.description)
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    // Creative type selector for creative content
                    if selectedFeature == .creativeContent {
                        Picker("Creative Type", selection: $selectedCreativeType) {
                            Text("Story").tag(CreativeType.story)
                            Text("Poem").tag(CreativeType.poem)
                            Text("Dialogue").tag(CreativeType.dialogue)
                            Text("Description").tag(CreativeType.description)
                        }
                        .pickerStyle(SegmentedPickerStyle())
                    }
                    
                    // Language selector for translation
                    if selectedFeature == .translation {
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Text("Detected Language:")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                                Spacer()
                                Text(getLanguageName(detectedLanguage))
                                    .font(.caption)
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 4)
                                    .background(Color.blue.opacity(0.1))
                                    .foregroundColor(.blue)
                                    .cornerRadius(8)
                            }
                            
                            Picker("Target Language", selection: $targetLanguage) {
                                Text("Spanish").tag("Spanish")
                                Text("French").tag("French")
                                Text("German").tag("German")
                                Text("Italian").tag("Italian")
                                Text("Portuguese").tag("Portuguese")
                                Text("Chinese").tag("Chinese")
                                Text("Japanese").tag("Japanese")
                            }
                            .pickerStyle(MenuPickerStyle())
                        }
                    }
                    
                    TextEditor(text: $inputText)
                        .frame(minHeight: 80)
                        .padding(8)
                        .background(Color.gray.opacity(0.1))
                        .cornerRadius(8)
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(Color.gray.opacity(0.3), lineWidth: 1)
                        )
                        .onTapGesture {
                            // Allow tapping to focus
                        }
                        .onChange(of: inputText) {
                            // Limit text length to prevent overwhelming the AI model
                            let maxLength = 2000
                            if inputText.count > maxLength {
                                inputText = String(inputText.prefix(maxLength))
                            }
                            
                            // Detect language for translation feature
                            if selectedFeature == .translation {
                                detectedLanguage = aiManager.detectLanguage(inputText)
                            }
                        }
                        .toolbar {
                            ToolbarItemGroup(placement: .keyboard) {
                                Spacer()
                                Button("Done") {
                                    UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil)
                                }
                            }
                        }
                    
                    // Load working example button
                    Button(action: {
                        if let example = workingExamples[selectedFeature] {
                            inputText = example
                        }
                    }) {
                        HStack {
                            Image(systemName: "lightbulb.fill")
                            Text("Load Working Example")
                        }
                        .foregroundColor(.blue)
                        .padding(.vertical, 8)
                    }
                }
                .padding(.horizontal)
                
                // Action Button
                Button(action: processRequest) {
                    HStack {
                        if aiManager.isProcessing {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                .scaleEffect(0.8)
                        } else {
                            Image(systemName: "wand.and.stars")
                        }
                        Text(aiManager.isProcessing ? "Processing..." : "Generate with Apple AI")
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(inputText.isEmpty ? Color.gray : Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(10)
                }
                .disabled(inputText.isEmpty || aiManager.isProcessing)
                .padding(.horizontal)
                
                // Output Section
                ScrollView {
                    VStack(alignment: .leading, spacing: 16) {
                        if !outputText.isEmpty {
                            OutputCardView(title: "AI Response", content: outputText)
                        }
                        
                        if !taskSuggestions.isEmpty {
                            TaskSuggestionsView(suggestions: taskSuggestions)
                        }
                        
                        if let entities = extractedEntities {
                            EntitiesView(entities: entities)
                        }
                        
                        if let classification = contentClassification {
                            ClassificationView(classification: classification)
                        }
                        
                        if !categorizationResults.isEmpty {
                            CategorizationResultsView(results: categorizationResults)
                        }
                        
                        if let error = aiManager.lastError {
                            ErrorCardView(error: error)
                        }
                    }
                    .padding(.horizontal)
                }
                
                Spacer()
            }
        }
        .onTapGesture {
            // Dismiss keyboard when tapping outside text fields
            UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil)
        }
        .navigationTitle("Apple Intelligence")
        .navigationBarTitleDisplayMode(.inline)
    }
    
    private func processRequest() {
        guard !inputText.isEmpty else { return }
        
        // Clear existing response before generating new one
        outputText = ""
        categorizationResults = []
        
        switch selectedFeature {
        case .textGeneration:
            aiManager.generateText(prompt: inputText) { result in
                outputText = result
            }
            
        case .summarization:
            aiManager.summarizeText(inputText) { result in
                outputText = result
            }
            
        case .taskSuggestions:
            aiManager.generateTaskSuggestions(from: inputText) { suggestions in
                taskSuggestions = suggestions
            }
            
        case .entityExtraction:
            aiManager.extractEntities(from: inputText) { entities in
                extractedEntities = entities
            }
            
        case .contentClassification:
            aiManager.classifyContent(inputText) { classification in
                contentClassification = classification
            }
            
        case .categorization:
            aiManager.classifyContent(inputText) { classification in
                if let classification = classification {
                    categorizationResults = [classification.category, classification.sentiment] + classification.topics
                }
            }
            
        case .creativeContent:
            aiManager.generateCreativeContent(type: selectedCreativeType, prompt: inputText) { result in
                outputText = result
            }
            
        case .translation:
            aiManager.translateText(inputText, to: targetLanguage) { result in
                outputText = result
            }
        }
    }
    
    private func getLanguageName(_ code: String) -> String {
        let locale = Locale(identifier: code)
        return locale.localizedString(forLanguageCode: code)?.capitalized ?? "Unknown"
    }
}


#Preview {
    if #available(iOS 26.0, *) {
        ContentView()
    } else {
        Text("iOS 26.0 required for Apple Intelligence")
    }
}
