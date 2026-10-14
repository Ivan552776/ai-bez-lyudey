import SwiftUI
import WebKit

enum SiteEnvironment: String, CaseIterable, Identifiable {
    case local, live

    var id: String { rawValue }
    var title: String { self == .local ? "На этом Mac" : "Живой сайт" }
    var symbol: String { self == .local ? "desktopcomputer" : "globe" }
    var url: URL {
        URL(string: self == .local
            ? "http://localhost:4376/ai-bez-lyudey/kursy/"
            : "https://ivan552776.github.io/ai-bez-lyudey/kursy/")!
    }
}

@MainActor
final class BrowserModel: NSObject, ObservableObject, WKNavigationDelegate, WKUIDelegate {
    let webView: WKWebView
    @Published var environment: SiteEnvironment = .local
    @Published var canGoBack = false
    @Published var canGoForward = false
    @Published var isLoading = false
    @Published var progress = 0.0
    @Published var errorMessage: String?
    private var observations: [NSKeyValueObservation] = []

    override init() {
        let configuration = WKWebViewConfiguration()
        configuration.allowsInlineMediaPlayback = true
        // Проверочный просмотр не должен сохранять входы и историю между запусками.
        configuration.websiteDataStore = .nonPersistent()
        webView = WKWebView(frame: .zero, configuration: configuration)
        super.init()
        webView.navigationDelegate = self
        webView.uiDelegate = self
        webView.allowsBackForwardNavigationGestures = true
        webView.isOpaque = false
        webView.backgroundColor = .systemBackground
        webView.scrollView.backgroundColor = .systemBackground
        #if DEBUG
        webView.isInspectable = true
        #endif
        observations = [
            webView.observe(\.canGoBack, options: [.new]) { [weak self] _, _ in
                DispatchQueue.main.async { self?.syncState() }
            },
            webView.observe(\.canGoForward, options: [.new]) { [weak self] _, _ in
                DispatchQueue.main.async { self?.syncState() }
            },
            webView.observe(\.isLoading, options: [.new]) { [weak self] _, _ in
                DispatchQueue.main.async { self?.syncState() }
            },
            webView.observe(\.estimatedProgress, options: [.new]) { [weak self] _, _ in
                DispatchQueue.main.async { self?.syncState() }
            }
        ]
        open(.local)
    }

    private func syncState() {
        canGoBack = webView.canGoBack
        canGoForward = webView.canGoForward
        isLoading = webView.isLoading
        progress = webView.estimatedProgress
    }

    func open(_ selection: SiteEnvironment) {
        environment = selection
        errorMessage = nil
        webView.load(URLRequest(url: selection.url, cachePolicy: .reloadIgnoringLocalCacheData,
                                timeoutInterval: 20))
    }

    func reload() {
        errorMessage = nil
        if webView.url == nil { open(environment) }
        else { webView.reloadFromOrigin() }
    }

    func webView(_ webView: WKWebView, didStartProvisionalNavigation navigation: WKNavigation!) {
        errorMessage = nil
    }

    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!,
                 withError error: Error) {
        show(error)
    }

    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
        show(error)
    }

    private func show(_ error: Error) {
        guard (error as NSError).code != NSURLErrorCancelled else { return }
        errorMessage = environment == .local
            ? "Проверь, что сервер на Mac работает на порту 4376. Или выбери живой сайт в нижнем меню."
            : "Проверь подключение к интернету и попробуй ещё раз."
        print("Ошибка просмотра сайта:", error.localizedDescription)
    }

    func webViewWebContentProcessDidTerminate(_ webView: WKWebView) {
        errorMessage = "iOS остановила страницу. Нажми «Обновить», чтобы открыть её снова."
    }

    func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction,
                 decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        guard let url = navigationAction.request.url else {
            decisionHandler(.cancel)
            return
        }
        // Обычные страницы остаются внутри просмотра, ссылки приложений открывает iOS.
        if ["https", "http", "about"].contains(url.scheme?.lowercased() ?? "") {
            decisionHandler(.allow)
        } else {
            decisionHandler(.cancel)
            UIApplication.shared.open(url)
        }
    }

    func webView(_ webView: WKWebView, createWebViewWith configuration: WKWebViewConfiguration,
                 for navigationAction: WKNavigationAction,
                 windowFeatures: WKWindowFeatures) -> WKWebView? {
        if navigationAction.targetFrame == nil { webView.load(navigationAction.request) }
        return nil
    }
}

private struct WebContent: UIViewRepresentable {
    let model: BrowserModel
    func makeUIView(context: Context) -> WKWebView { model.webView }
    func updateUIView(_ uiView: WKWebView, context: Context) {}
}

struct BrowserView: View {
    @StateObject private var browser = BrowserModel()

    var body: some View {
        WebContent(model: browser)
            .overlay(alignment: .top) {
                if browser.isLoading {
                    ProgressView(value: browser.progress)
                        .progressViewStyle(.linear)
                        .accessibilityLabel("Загрузка страницы")
                }
            }
            .overlay {
                if let message = browser.errorMessage {
                    ContentUnavailableView {
                        Label("Страница не открылась", systemImage: "wifi.exclamationmark")
                    } description: {
                        Text(message)
                    } actions: {
                        Button("Обновить", action: browser.reload)
                            .buttonStyle(.borderedProminent)
                            .frame(minHeight: 44)
                    }
                    .background(Color(uiColor: .systemBackground))
                }
            }
            .safeAreaInset(edge: .bottom, spacing: 0) {
                HStack(spacing: 4) {
                    Button { browser.webView.goBack() } label: {
                        Image(systemName: "chevron.backward").frame(width: 44, height: 44)
                    }
                    .disabled(!browser.canGoBack)
                    .accessibilityLabel("Назад")

                    Button { browser.webView.goForward() } label: {
                        Image(systemName: "chevron.forward").frame(width: 44, height: 44)
                    }
                    .disabled(!browser.canGoForward)
                    .accessibilityLabel("Вперёд")

                    Spacer(minLength: 0)
                    Menu {
                        ForEach(SiteEnvironment.allCases) { option in
                            Button { browser.open(option) } label: {
                                Label(option.title, systemImage: option == browser.environment
                                      ? "checkmark" : option.symbol)
                            }
                        }
                    } label: {
                        Label(browser.environment.title, systemImage: browser.environment.symbol)
                            .font(.subheadline)
                            .lineLimit(1)
                            .frame(minHeight: 44)
                    }
                    .accessibilityLabel("Источник: \(browser.environment.title)")
                    .accessibilityHint("Выбрать локальную версию или живой сайт")
                    Spacer(minLength: 0)

                    Button(action: browser.reload) {
                        Image(systemName: "arrow.clockwise").frame(width: 44, height: 44)
                    }
                    .accessibilityLabel("Обновить")
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(.bar)
            }
            .tint(.accentColor)
    }
}

