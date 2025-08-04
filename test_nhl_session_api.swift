import Foundation
import Network

// MARK: - Data Models
struct SessionResponse: Codable {
    let data: [SessionData]
    let total: Int
}

struct SessionData: Codable {
    let logoutUrl: String
    let userProfile: UserProfile
}

struct UserProfile: Codable {
    let affiliatedNhlTeam: String?
    let email: String
    let firstName: String
    let id: String
    let lastName: String
    let permissions: [String]
    let roles: [String]
}

// MARK: - Network Service
class NHLSessionService {
    private let session = URLSession.shared
    private let baseURL = "https://videocast.nhl.com"
    
    // Hardcoded session cookie from successful curl request
    private let sessionCookie = "_shibsession_64656661756c7468747470733a2f2f766964656f636173742e6e686c2e636f6d=_21f2b53c523f382640225dca9ab289a3"
    
    func validateSession() async throws -> SessionResponse {
        guard let url = URL(string: "\(baseURL)/rest/session?include=userProfile&include=appMetadata") else {
            throw NetworkError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        
        // Add headers to match successful curl request
        request.setValue("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Safari/605.1.15", forHTTPHeaderField: "User-Agent")
        request.setValue("application/json, text/plain, */*", forHTTPHeaderField: "Accept")
        request.setValue("en-US,en;q=0.9", forHTTPHeaderField: "Accept-Language")
        request.setValue("gzip, deflate, br", forHTTPHeaderField: "Accept-Encoding")
        request.setValue("no-cache", forHTTPHeaderField: "Cache-Control")
        request.setValue("no-cache", forHTTPHeaderField: "Pragma")
        request.setValue("same-origin", forHTTPHeaderField: "Sec-Fetch-Site")
        request.setValue("cors", forHTTPHeaderField: "Sec-Fetch-Mode")
        request.setValue("empty", forHTTPHeaderField: "Sec-Fetch-Dest")
        request.setValue("https://videocast.nhl.com/events/2025-05-14", forHTTPHeaderField: "Referer")
        request.setValue("u=3, i", forHTTPHeaderField: "Priority")
        
        // Add the authentication cookie
        request.setValue(sessionCookie, forHTTPHeaderField: "Cookie")
        
        print("🌐 Requesting session validation with full URL: \(url.absoluteString)")
        print("📋 Request headers:")
        request.allHTTPHeaderFields?.forEach { key, value in
            print("  \(key): \(value)")
        }
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw NetworkError.invalidResponse
        }
        
        print("📡 Response status code: \(httpResponse.statusCode)")
        print("📄 Response headers:")
        httpResponse.allHeaderFields.forEach { key, value in
            print("  \(key): \(value)")
        }
        
        guard httpResponse.statusCode == 200 else {
            let responseString = String(data: data, encoding: .utf8) ?? "No response body"
            print("❌ Error response body: \(responseString)")
            throw NetworkError.httpError(httpResponse.statusCode)
        }
        
        let responseString = String(data: data, encoding: .utf8) ?? "No response body"
        print("✅ Raw response: \(responseString)")
        
        do {
            let sessionResponse = try JSONDecoder().decode(SessionResponse.self, from: data)
            print("🎉 Successfully parsed session response:")
            print("  User: \(sessionResponse.data.first?.userProfile.firstName ?? "Unknown") \(sessionResponse.data.first?.userProfile.lastName ?? "")")
            print("  Email: \(sessionResponse.data.first?.userProfile.email ?? "Unknown")")
            print("  Roles: \(sessionResponse.data.first?.userProfile.roles ?? [])")
            print("  Permissions: \(sessionResponse.data.first?.userProfile.permissions ?? [])")
            return sessionResponse
        } catch {
            print("❌ JSON parsing error: \(error)")
            throw NetworkError.decodingError(error)
        }
    }
}

// MARK: - Error Types
enum NetworkError: LocalizedError {
    case invalidURL
    case invalidResponse
    case httpError(Int)
    case decodingError(Error)
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .invalidResponse:
            return "Invalid response"
        case .httpError(let code):
            return "HTTP error with status code: \(code)"
        case .decodingError(let error):
            return "Decoding error: \(error.localizedDescription)"
        }
    }
}

// MARK: - Test Runner
class NHLSessionAPITest {
    private let service = NHLSessionService()
    
    func runHardcodedTest() async {
        print("🚀 Starting NHL Session API Hardcoded Test")
        print("=" * 50)
        
        do {
            let sessionResponse = try await service.validateSession()
            
            print("\n✅ Test PASSED!")
            print("📊 Test Results:")
            print("  Total sessions: \(sessionResponse.total)")
            
            if let userData = sessionResponse.data.first {
                print("  🧑‍💼 User Profile:")
                print("    Name: \(userData.userProfile.firstName) \(userData.userProfile.lastName)")
                print("    Email: \(userData.userProfile.email)")
                print("    ID: \(userData.userProfile.id)")
                print("    NHL Team: \(userData.userProfile.affiliatedNhlTeam ?? "None")")
                print("    Roles: \(userData.userProfile.roles.joined(separator: ", "))")
                print("    Permissions: \(userData.userProfile.permissions.joined(separator: ", "))")
                print("  🔗 Logout URL: \(userData.logoutUrl)")
            }
            
        } catch {
            print("\n❌ Test FAILED!")
            print("🔥 Error: \(error.localizedDescription)")
            
            if let networkError = error as? NetworkError {
                switch networkError {
                case .httpError(let code):
                    print("💡 HTTP Status Code: \(code)")
                    if code == 302 {
                        print("💡 Suggestion: Session may have expired or authentication is required")
                    }
                case .decodingError(let decodingError):
                    print("💡 JSON Decoding Issue: \(decodingError)")
                default:
                    break
                }
            }
        }
        
        print("\n" + "=" * 50)
        print("🏁 Test completed")
    }
}

// MARK: - Main Test Execution
@main
struct NHLSessionAPITestRunner {
    static func main() async {
        let test = NHLSessionAPITest()
        await test.runHardcodedTest()
    }
}

// MARK: - String Extension for Repeat
extension String {
    static func * (left: String, right: Int) -> String {
        return String(repeating: left, count: right)
    }
}