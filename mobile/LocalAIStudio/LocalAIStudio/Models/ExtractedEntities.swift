import FoundationModels

@Generable
struct ExtractedEntities {
    let people: [String]
    let places: [String]
    let organizations: [String]
    let events: [String]
}
