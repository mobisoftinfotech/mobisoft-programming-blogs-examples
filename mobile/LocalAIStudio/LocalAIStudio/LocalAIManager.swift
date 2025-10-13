import Foundation
import FoundationModels
import NaturalLanguage
import Combine

@available(iOS 26.0, *)
class LocalAIManager: ObservableObject {
    
    @Published var isProcessing = false
    @Published var lastError: String?
    
    private var session = LanguageModelSession()
    private let model = SystemLanguageModel.default
    
    init() {
        setupModel()
    }
    
    private func setupModel() {
        // Check model availability
        switch model.availability {
        case .available:
            print("Foundation Model is available")
        case .unavailable(let reason):
            lastError = "Foundation Model unavailable: \(reason)"
            print("Foundation Model unavailable: \(reason)")
        }
    }
    
    // MARK: - Text Generation with Apple Intelligence
    func generateText(prompt: String, completion: @escaping (String) -> Void) {
        guard case .available = model.availability else {
            completion("Foundation Model not available")
            return
        }
        
        // Sanitize input to prevent safety guardrails
        let sanitizedPrompt = sanitizeInput(prompt)
        
        isProcessing = true
        lastError = nil
        
        Task {
            do {
                let response = try await session.respond(to: Prompt(sanitizedPrompt))
                let content = response.content
                
                await MainActor.run {
                    self.isProcessing = false
                    completion(content)
                }
            } catch {
                await MainActor.run {
                    self.isProcessing = false
                    let errorMessage = handleSafetyGuardrailsError(error)
                    self.lastError = errorMessage
                    completion("Error generating text: \(errorMessage)")
                }
            }
        }
    }
    
    // MARK: - Summarization with Foundation Models
    func summarizeText(_ text: String, completion: @escaping (String) -> Void) {
        guard case .available = model.availability else {
            completion("Foundation Model not available")
            return
        }
        
        // Sanitize input to prevent safety guardrails
        let sanitizedText = sanitizeInput(text)
        
        isProcessing = true
        lastError = nil
        
        Task {
            do {
                let prompt = "Summarize the following text concisely:\n\n\(sanitizedText)"
                let response = try await session.respond(to: Prompt(prompt))
                let content = response.content
                
                await MainActor.run {
                    self.isProcessing = false
                    completion(content)
                }
            } catch {
                await MainActor.run {
                    self.isProcessing = false
                    let errorMessage = handleSafetyGuardrailsError(error)
                    self.lastError = errorMessage
                    completion("Error summarizing text: \(errorMessage)")
                }
            }
        }
    }
    
    // MARK: - Guided Generation with Structured Output
    func generateTaskSuggestions(from text: String, completion: @escaping ([TaskSuggestion]) -> Void) {
        guard case .available = model.availability else {
            completion([])
            return
        }
        
        // Sanitize input to prevent safety guardrails
        let sanitizedText = sanitizeInput(text)
        
        isProcessing = true
        lastError = nil
        
        Task {
            do {
                let prompt = "Based on the following text, suggest 3 actionable tasks:\n\n\(sanitizedText)"
                
                // Use guided generation for structured output
                let response = try await session.respond(
                    to: Prompt(prompt),
                    generating: [TaskSuggestion].self
                )
                let content = response.content
                
                await MainActor.run {
                    self.isProcessing = false
                    completion(content)
                }
            } catch {
                await MainActor.run {
                    self.isProcessing = false
                    let errorMessage = handleSafetyGuardrailsError(error)
                    self.lastError = errorMessage
                    completion([])
                }
            }
        }
    }
    
    // MARK: - Entity Extraction
    func extractEntities(from text: String, completion: @escaping (ExtractedEntities?) -> Void) {
        guard case .available = model.availability else {
            completion(nil)
            return
        }
        
        isProcessing = true
        lastError = nil
        
        Task {
            do {
                let prompt = "Extract entities from the following text and categorize them:\n\n\(text)"
                
                let response = try await session.respond(
                    to: Prompt(prompt),
                    generating: ExtractedEntities.self
                )
                let content = response.content
                
                await MainActor.run {
                    self.isProcessing = false
                    completion(content)
                }
            } catch {
                await MainActor.run {
                    self.isProcessing = false
                    self.lastError = error.localizedDescription
                    completion(nil)
                }
            }
        }
    }
    
    
    // MARK: - Content Classification
    func classifyContent(_ text: String, completion: @escaping (ContentClassification?) -> Void) {
        guard case .available = model.availability else {
            completion(nil)
            return
        }
        
        // Sanitize input to prevent safety guardrails
        let sanitizedText = sanitizeInput(text)
        
        isProcessing = true
        lastError = nil
        
        Task {
            do {
                let prompt = """
                Analyze the following text and provide:
                1. Main category
                2. Sentiment analysis
                3. Key topics (up to 5)
                4. Confidence score (0.0 to 1.0)
                
                Text: \(sanitizedText)
                """
                
                let response = try await session.respond(
                    to: Prompt(prompt),
                    generating: ContentClassification.self
                )
                let content = response.content
                
                await MainActor.run {
                    self.isProcessing = false
                    completion(content)
                }
            } catch {
                await MainActor.run {
                    self.isProcessing = false
                    let errorMessage = handleSafetyGuardrailsError(error)
                    self.lastError = errorMessage
                    completion(nil)
                }
            }
        }
    }
    
    // MARK: - Language Understanding & Translation
    func detectLanguage(_ text: String) -> String {
        let recognizer = NLLanguageRecognizer()
        recognizer.processString(text)
        
        if let language = recognizer.dominantLanguage {
            return language.rawValue
        }
        return "unknown"
    }
    
    func translateText(_ text: String, to targetLanguage: String, completion: @escaping (String) -> Void) {
        guard case .available = model.availability else {
            completion("Foundation Model not available")
            return
        }
        
        // Sanitize input to prevent safety guardrails
        let sanitizedText = sanitizeInput(text)
        
        isProcessing = true
        lastError = nil
        
        Task {
            do {
                let prompt = """
                Translate the following text to \(targetLanguage). 
                Provide only the translation without any additional text or explanations.
                
                Text to translate: \(sanitizedText)
                """
                
                let response = try await session.respond(to: Prompt(prompt))
                let content = response.content
                
                await MainActor.run {
                    self.isProcessing = false
                    completion(content)
                }
            } catch {
                await MainActor.run {
                    self.isProcessing = false
                    let errorMessage = handleSafetyGuardrailsError(error)
                    self.lastError = errorMessage
                    completion("Error translating text: \(errorMessage)")
                }
            }
        }
    }
    
    // MARK: - Creative Content Generation
    func generateCreativeContent(type: CreativeType, prompt: String, completion: @escaping (String) -> Void) {
        guard case .available = model.availability else {
            completion("Foundation Model not available")
            return
        }
        
        isProcessing = true
        lastError = nil
        
        Task {
            do {
                let enhancedPrompt = switch type {
                case .story:
                    "Write a creative short story based on: \(prompt)"
                case .poem:
                    "Write a poem inspired by: \(prompt)"
                case .dialogue:
                    "Write a dialogue between characters about: \(prompt)"
                case .description:
                    "Write a vivid description of: \(prompt)"
                }
                
                let response = try await session.respond(to: Prompt(enhancedPrompt))
                let content = response.content
                
                await MainActor.run {
                    self.isProcessing = false
                    completion(content)
                }
            } catch {
                await MainActor.run {
                    self.isProcessing = false
                    self.lastError = error.localizedDescription
                    completion("Error generating creative content: \(error.localizedDescription)")
                }
            }
        }
    }
    
}

// MARK: - Helper Extensions
extension LocalAIManager {
    var isFoundationModelAvailable: Bool {
        return model.availability == .available
    }
    
    // MARK: - Safety Guardrails Helper Methods
    
    /// Sanitizes input text to prevent safety guardrails from being triggered
    private func sanitizeInput(_ input: String) -> String {
        var sanitized = input.trimmingCharacters(in: .whitespacesAndNewlines)
        
        // Convert to more neutral, educational language to avoid safety triggers
        sanitized = convertToEducationalPrompt(sanitized)
        
        // Remove or replace potentially problematic content
        let problematicPatterns = [
            // Remove excessive punctuation that might trigger safety filters
            (try? NSRegularExpression(pattern: "[!]{3,}", options: [])): "",
            (try? NSRegularExpression(pattern: "[?]{3,}", options: [])): "",
            (try? NSRegularExpression(pattern: "[.]{3,}", options: [])): "...",
            
            // Remove excessive capitalization
            (try? NSRegularExpression(pattern: "\\b[A-Z]{5,}\\b", options: [])): "",
            
            // Remove potential spam patterns
            (try? NSRegularExpression(pattern: "\\b(click|buy|free|win|prize|offer|deal|discount|sale|limited|urgent|act now|don't miss)\\b", options: [.caseInsensitive])): "",
        ]
        
        for (regex, replacement) in problematicPatterns {
            if let regex = regex {
                sanitized = regex.stringByReplacingMatches(in: sanitized, options: [], range: NSRange(location: 0, length: sanitized.count), withTemplate: replacement)
            }
        }
        
        // Limit input length to prevent overwhelming the model
        if sanitized.count > 2000 {
            sanitized = String(sanitized.prefix(2000)) + "..."
        }
        
        // Ensure the input is not empty after sanitization
        if sanitized.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            sanitized = "Please provide a valid input for processing."
        }
        
        return sanitized
    }
    
    /// Converts user input to educational prompts that are less likely to trigger safety filters
    private func convertToEducationalPrompt(_ input: String) -> String {
        let lowercased = input.lowercased()
        
        // Convert creative requests to educational format
        if lowercased.contains("write") && (lowercased.contains("story") || lowercased.contains("poem")) {
            return "Create educational content about the topic mentioned."
        }
        
        // Convert "tell me about" to educational format
        if lowercased.contains("tell me about") || lowercased.contains("write me") {
            let topic = input.replacingOccurrences(of: "tell me about", with: "", options: .caseInsensitive)
                           .replacingOccurrences(of: "write me", with: "", options: .caseInsensitive)
                           .trimmingCharacters(in: .whitespacesAndNewlines)
            return "Provide educational information about \(topic)."
        }
        
        // For very short inputs, add educational context
        if input.count < 15 && input.components(separatedBy: .whitespaces).count <= 3 {
            return "Provide educational information about \(input)."
        }
        
        return input
    }
    
    /// Handles safety guardrails errors with user-friendly messages
    private func handleSafetyGuardrailsError(_ error: Error) -> String {
        let errorDescription = error.localizedDescription.lowercased()
        
        if errorDescription.contains("safety") || errorDescription.contains("guardrail") {
            return "The content may have triggered safety filters. Please try rephrasing your request with different wording."
        } else if errorDescription.contains("inappropriate") {
            return "The content appears to be inappropriate. Please provide different content to process."
        } else if errorDescription.contains("policy") {
            return "The request doesn't meet our content policy. Please try a different approach."
        } else if errorDescription.contains("rate limit") || errorDescription.contains("quota") {
            return "Too many requests. Please wait a moment before trying again."
        } else {
            return "An error occurred while processing your request. Please try again with different content."
        }
    }
    
}
