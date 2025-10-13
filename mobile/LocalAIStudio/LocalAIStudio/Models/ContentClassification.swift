import FoundationModels

@Generable
struct ContentClassification {
    let category: String
    let sentiment: String
    let topics: [String]
    let confidence: Double
}
