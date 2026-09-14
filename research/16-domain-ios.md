# 16 · Domain pack: native Swift iOS apps

Researcher report for the `/drive` skill. Date: 2026-09-14. Scope: what the skill must know to have agents set up, build, run, test, visually verify and eventually ship a native iOS app on a Mac without anyone opening the Xcode GUI. The fashion app in the brief is only an illustration of the shape; nothing here was built, and no project, Swift file or probe app was created. Checks were read-only (`xcodebuild -version`, `xcodebuild -help`, `xcrun simctl help`, `xcrun xcresulttool help`, `xcodegen --version`, `swift --version`, runtime and device listings, one Simulator MCP preflight call) plus Apple documentation and GitHub pages. A temporary directory under `/private/tmp` held two downloaded release-note JSON files and was deleted.

This report deliberately does not repeat two neighbours. Report 08 (test strategy) already covers the three iOS test lanes, the core `xcodebuild test` and `xcresulttool` commands, snapshot tolerances, the `performAccessibilityAudit` test, and the end-to-end recipe against Cloudflare. Report 09 (UI vision verification) already covers the design contract, the capture matrix script, the state harness launch arguments, HIG accessibility and typography numbers, and the vision rubric. Where this report touches those topics it adds or corrects rather than restates, and it says so.

---

## 1. Executive opinion

The iOS pack has one job: make the Apple toolchain behave like a deterministic command-line system that an agent can drive, and refuse to call anything proven that did not run on a named simulator, from a named build, against a named backend.

Four decisions carry most of the value. First, generate the project from text. XcodeGen (2.46.0, July 2026) with a `project.yml` and a local Swift package holding the feature modules is the default, because agents edit YAML and `Package.swift` reliably and corrupt `project.pbxproj` unreliably; the `.xcodeproj` becomes a build artifact. Existing apps keep whatever format they already use. Second, put every build, test and capture behind a handful of repo scripts that pin the Xcode path, the simulator by UDID, the derived-data directory and the result-bundle path, and that fail when zero tests ran. Agents who type `xcodebuild` from memory produce most iOS failures: wrong destination, stale products, filtered test runs that execute nothing. Third, treat the Simulator MCP as a convenience for exploration and evidence capture, never as the only path to a gate. It is broken on this Mac today with an `xcode-select` error that needs `sudo`, and the same class of breakage will recur after every Xcode update. Fourth, keep the architecture boring and testable: SwiftUI with `@Observable` models, main-actor isolation by default with explicit escapes, a generated API client checked into the repo, a real SQLite or SwiftData store in tests rather than a fake, and every screen state reachable by launch argument.

Local Proof for iOS means the generated project builds for the simulator at HEAD, the fast and UI lanes pass with a non-zero executed count, and accessibility audits pass. Live Proof means the HEAD build, installed on a named simulator and pointed at the deployed backend, showed server-sourced values in its accessibility tree and in screenshots that a separate reviewer graded. Features the simulator cannot exercise (camera, passkeys on some runtimes, real background scheduling) are listed as unproven, never silently assumed.

---

## 2. What the post says, and a critique

The post never mentions iOS, but three of its claims land hard on this domain.

**"Self-verification via vision" (step 13).** Right in spirit, underspecified for native apps. A screenshot of an iOS simulator is only evidence when three things are pinned: which device (with two simulators booted, `simctl io booted` silently picks one, as report 09 proved on this Mac), which build (the simulator happily keeps running the previous install after a failed build), and which state (fixtures versus live data). The post's loop of maker renders, verifier reads the screenshot does not survive contact with Xcode unless the skill adds a build stamp, a UDID and a data-source label to every image. For native apps the accessibility tree is also a better oracle than pixels for anything textual; the MCP's `inspect` returns labels, values and frames, and that is what a verifier should assert against, with vision reserved for layout and taste.

**"Worktrees for parallel safety" (step 8).** True for source files, misleading for iOS. Worktrees isolate the checkout but not the simulator, the CoreSimulator service, the default DerivedData folder, or the Swift package cache. Two agents in two worktrees running UI tests on the same booted iPhone will kill each other's app process, and two builds sharing default DerivedData can pick up each other's products. The iOS pack has to add per-worktree `-derivedDataPath`, one simulator device per concurrent agent, and a rule that UI lanes are serialized per device. Report 12 covers worktrees generally; this is the iOS-specific addendum.

**"Routines for days-long orchestration" and "Running long sessions on a laptop" as a mistake (steps 9 and §).** For iOS this advice is wrong. Anthropic-hosted cloud runs are Linux containers; they cannot run Xcode, the iOS Simulator, or `xcodebuild`. Every build, test and screenshot in this domain requires a Mac with Xcode, so the long-running iOS loop must run on the owner's Mac (or a Mac CI runner the owner sets up). A cloud routine can review diffs or regenerate an OpenAPI document, but it cannot produce iOS evidence, and a skill that schedules an iOS verification in the cloud will report success on a job that never touched a simulator.

**Model routing (step 4).** The post's idea that volume work goes to cheaper models is sound, but Swift 6 strict-concurrency errors are not volume work. They look mechanical and are not: the cheap fix (`@unchecked Sendable`, `nonisolated(unsafe)`, `MainActor.assumeIsolated`) silences the compiler and moves the data race to runtime. The skill should route concurrency diagnostics to `opus` and forbid those escape hatches without a written justification.

**"Verifier sub-agent beats self-critique" (step 6).** Right, and on iOS the verifier needs its own capture. A maker that hands over its own screenshots can hand over the wrong device, the wrong appearance, or an image from before the fix. Report 09 already requires the reviewer to capture for itself; this pack supplies the scripts that make that cheap.

---

## 3. Verified facts

Tags: **[local]** checked on this Mac today with a read-only command; **[verified]** read today on the cited page; **[source claim]** stated by a secondary source and not independently confirmed; **[opinion]** mine.

### 3.1 Toolchain on this Mac

1. `xcodebuild -version` prints Xcode 27.0, build 27A5209h; `xcode-select -p` prints `/Applications/Xcode.app/Contents/Developer`; `swift --version` prints Apple Swift 6.4 (swiftlang-6.4.0.23.5), target `arm64-apple-macosx27.0.0`. **[local]**
2. A second Xcode is installed at `/Applications/Xcode-26.app` (Xcode 26.6, build 17F113). Any script that relies on whichever `xcodebuild` is first on the path, or on `xcode-select` state inside another process, can pick the wrong one. **[local]**
3. Installed simulator runtimes are two iOS 26.4 builds (23E244 and 23E254a) that share the identifier `com.apple.CoreSimulator.SimRuntime.iOS-26-4`; there is no iOS 27 runtime. Available devices include iPhone 17 Pro (booted), iPhone 17 Pro Max, iPhone 17e, iPhone Air, iPhone 17, iPad Pro 13-inch (M5), iPad Pro 11-inch (M5) (booted), iPad mini (A17 Pro), iPad Air 11 and 13 (M4), iPad (A16). Device types for iPhone SE (3rd generation) and iPhone 16e exist but no devices of those types are created. **[local]** Consequence: a destination written as `OS=26.4` is ambiguous between two runtimes; resolve by UDID.
4. Default DerivedData at `~/Library/Developer/Xcode/DerivedData` holds 4.5 GB across 14 project folders; no custom location is configured. **[local]**
5. XcodeGen 2.46.0 is installed at `/opt/homebrew/bin/xcodegen`; Tuist is not installed. **[local]**
6. Xcode 27 RC ships Swift 6.4 and the iOS 27 SDK, requires macOS Tahoe 26.6 or later, and supports iOS deployment targets 15 to 27; Xcode 26.6 supports iOS 15 to 26.5 with Swift 6.3. **[verified]** https://developer.apple.com/support/xcode/ and https://developer.apple.com/documentation/xcode-release-notes/xcode-27-release-notes
7. Tuist users hit the raised minimum deployment target in the Xcode 27 beta: external packages declaring iOS 13 were rejected with "the range of supported deployment target versions is 15.0 to 27.0.x". **[verified]** https://github.com/tuist/tuist/issues/11163 (closed). The same error will hit any project, generated or not, that pulls an old package.

### 3.2 Xcode 27 and iOS 27 changes that matter to agents

8. Testing (Xcode 27 notes): configurable crash severity for UI tests in the test plan; a launch-test template using `runsForEachTargetApplicationUIConfiguration`; cross-framework assertion interoperability setting; `XCUIVoiceOverService`; Test Repetition Mode repeats individual Swift Testing cases; parameterized test links include an argument hash; Swift Testing better attributes issues raised on detached tasks and background threads. **[verified]** release notes above. (Report 08 lists most of these; they are repeated here only because the gate design below depends on them.)
9. Simulator: `simctl reboot` is new; runtimes ship a pre-built dyld cache for faster first launch; Accessibility Inspector can inspect simulator elements again (it could not in earlier betas); known issue that deleted runtimes can reappear after reboot. **[verified]** release notes above.
10. Previews: `PreviewProvider` is deprecated; `#Preview` code now runs on the main actor; previews gained `#Preview(arguments:)`, a Resizable Canvas, and localization and contrast overrides; Xcode exposes `RenderPreview` and `ExecuteSnippet` MCP tools. **[verified]** release notes above. These MCP tools live inside Xcode's own agent integration; they are not the Claude Code Simulator MCP.
11. Swift Package Manager: `swift test` summarizes failures and supports `--maximum-repetitions` with `--repeat-until pass|fail`. **[verified]** release notes above.
12. Swift compiler: the dependency scanner now requires unique Clang module names across a scan, a known source break for vendored module maps; SE-0508 source break for computed properties with `init` accessors. **[verified]** release notes above.
13. iOS 27 SDK: "Apps built with the latest SDK must adopt the scene-based life cycle or they fail to launch", and apps "are required to include a launch screen" via `UILaunchScreen` or a storyboard key. **[verified]** https://developer.apple.com/documentation/ios-ipados-release-notes/ios-ipados-27-release-notes (read through the JSON data endpoint).
14. iOS 27 SDK: `@State` is reimplemented as a macro that evaluates its initial value once; it is "largely source compatible" but some patterns that assign both a declaration default and an initializer value no longer compile. `AsyncImage` now honours HTTP caching and accepts a custom `URLSession`. A SwiftData deadlock between `@Query` and a background `ModelActor` save was fixed. **[verified]** same page.
15. Liquid Glass: several secondary sources say the `UIDesignRequiresCompatibility` opt-out is ignored when building with the iOS 27 SDK. The iOS 27 release notes I read contain no mention of that key. **[source claim]** https://daily.dev/posts/your-liquid-glass-opt-out-just-expired-here-s-the-audit-i-d-run-this-week-jl3jahone , https://byteiota.com/liquid-glass-ios27-mandatory/ . Treat as true for design purposes (design for Liquid Glass) and verify on the first build.
16. Icon Composer 2.0 renders for both the 2026 and 2027 design generations; one `.icon` file added to the project covers all OS versions. **[verified]** Xcode 27 release notes. Icon Composer icons are a single layered 1024-point source with default, dark, clear and tinted appearances. **[source claim]** https://useyourloaf.com/blog/adding-icon-composer-icons-to-xcode/

### 3.3 Command-line surface (all from local help output)

17. `xcodebuild` supports `-derivedDataPath`, `-clonedSourcePackagesDirPath`, `-packageCachePath`, `-onlyUsePackageVersionsFromResolvedFile`, `-disableAutomaticPackageResolution`, `-skipPackagePluginValidation`, `-skipMacroValidation` (both flagged in help as a security risk for untrusted sources), `-destination-timeout`, `-showdestinations`, `-showTestPlans`, `-showBuildSettings -json`, `-json`, `-resultBundlePath`, `-resultStreamPath`, `-testProductsPath`, `-enableThreadSanitizer`, `-enableAddressSanitizer`, `-showBuildTimingSummary`, `-downloadPlatform iOS [-buildVersion]`, `-importPlatform`, and `-allowProvisioningUpdates` with `-authenticationKeyPath`, `-authenticationKeyID`, `-authenticationKeyIssuerID`. **[local]**
18. `xcodebuild` test enumeration: `-enumerate-tests`, `-test-enumeration-style flat|hierarchical`, `-test-enumeration-format text|json`, `-test-enumeration-output-path <path|->`. Also `-only-test-configuration`, `-skip-test-configuration`, `-testLanguage`, `-testRegion`, `-test-iterations`, `-retry-tests-on-failure`, `-run-tests-until-failure`, `-test-repetition-relaunch-enabled`, `-collect-test-diagnostics on-failure|never`. **[local]** Enumeration is how a gate proves a filter selects what it claims before it runs.
19. `xcodebuild -exportArchive` method names: `app-store` is deprecated in favour of `app-store-connect`, `ad-hoc` in favour of `release-testing`, `development` in favour of `debugging`. **[local]** (`xcodebuild -help` export options text.)
20. `xcresulttool` (version 25090) subcommands: `get test-results summary|tests|test-details|activities|insights|metrics`, `get build-results`, `get log`, `get content-availability`, `export`, `merge`, `compare`; `get object` is deprecated and needs `--legacy`; `--schema` prints the JSON schema of each output. **[local]**
21. `simctl` subcommands include `addmedia` (photos, live photos, videos, vCard contacts into the device library), `appinfo`, `clone`, `create`, `erase`, `get_app_container <device> <bundle> [app|data|groups|<group id>]`, `getenv`, `install`, `keychain <device> add-root-cert|add-cert|reset`, `launch`, `listapps`, `location`, `openurl`, `pbcopy`/`pbpaste`, `privacy`, `push`, `reboot`, `runtime`, `spawn`, `status_bar`, `terminate`, `ui`, `uninstall`, `upgrade`. **[local]**
22. `simctl privacy <device> grant|revoke|reset <service> <bundle>`; services are `all`, `calendar`, `contacts-limited`, `contacts`, `location`, `location-always`, `photos-add`, `photos`, `media-library`, `microphone`, `motion`, `reminders`, `siri`. There is no camera service. Help text warns: "Using this command to bypass those requirements can mask bugs", meaning missing usage-description keys. **[local]**
23. `simctl push <device> [<bundle>] (<json file> | -)`: payload must be a top-level object with an `aps` key, 4096 bytes or less; a `Simulator Target Bundle` key can replace the bundle argument; only app remote pushes are supported, not VoIP, complication or File Provider. **[local]**
24. `simctl launch` accepts `--terminate-running-process`, `--console-pty`, `--stdout=<path>`, `--stderr=<path>`, and passes environment variables set as `SIMCTL_CHILD_<NAME>` in the calling shell. **[local]**
25. `simctl ui <device> appearance light|dark`, `content_size <category|increment|decrement>`, `increase_contrast enabled|disabled`; `status_bar <device> override --time --dataNetwork --wifiMode --wifiBars --cellularMode --cellularBars --operatorName --batteryState --batteryLevel`, plus `list` and `clear`. **[local]**

### 3.4 The iOS Simulator MCP

26. Tool schemas: `build` (`build`, `build_status`; takes an absolute `project_path` or `workspace_path`, `scheme`, `configuration`, `device`) returns a build id and then the built `.app` path; its description states that headless builds skip Xcode's Swift-macro trust prompt, so approving a build also trusts the project's package macros. `control` offers `attach`, `launch`, `screenshot`, `inspect`, `tap`, `swipe`, `touch_path`, `touch2_path`, `text`, `button`, `open_url`, `detach`; coordinates are in device points; a swipe starting within 4 pt of an edge performs the OS edge gesture. **[local]** (schemas loaded this session)
27. Preflight today: `control inspect` on the booted iPhone 17 Pro returned "'inspect' is not available right now. Use 'screenshot' instead."; `control screenshot` then returned "Xcode is installed but not selected. Run `sudo xcode-select -s /Applications/Xcode.app/Contents/Developer`". This matches report 09's finding and persists even though the shell's `xcode-select -p` is already that path. **[local]** The owner must run that command once; the skill cannot.
28. The Claude Code documentation index (`https://code.claude.com/docs/en/llms.txt`) has no page mentioning the simulator, iOS or Xcode, so the MCP's behaviour is documented only by its tool schemas and error messages. **[local]** (grep of the fetched index)
29. XcodeBuildMCP v2.7.0 (July 2026, now under `getsentry`) offers build, test, simulator management, UI automation, logs, screenshots and a `describe_ui` accessibility dump, both as an MCP server and as a CLI, installable with Homebrew or npm; it skips macro validation and sends error telemetry to Sentry unless disabled. **[verified]** https://github.com/getsentry/XcodeBuildMCP

### 3.5 Project generation

30. XcodeGen 2.46.0 (2026-07-16) added Swift package traits and preserves target declaration order; 2.45.x fixed several synced-folder bugs. **[verified]** https://github.com/yonaskolb/XcodeGen/releases
31. XcodeGen spec: `type: syncedFolder` sources need `projectFormat: xcode16_0` or later (formats listed up to `xcode16_3`); local packages are declared as `packages: <Name>: path: <dir>` with optional `group`; targets depend on `package:` plus `product:` or `products:`; target types include `application`, `bundle.unit-test`, `bundle.ui-testing`; `info:` and `entitlements:` generate plists from `properties`; schemes take `test: testPlans: [{path, defaultPlan}]`; "test plans are not generated by XcodeGen and must be created in Xcode and checked in"; `options.preGenCommand` and `postGenCommand` exist. **[verified]** https://github.com/yonaskolb/XcodeGen/blob/master/Docs/ProjectSpec.md
32. A search of XcodeGen issues for "Xcode 27" found no open compatibility reports. **[local]** (`gh api search/issues`) Absence of reports is weak evidence; the first `xcodegen generate && xcodebuild -list` in a project is the real check.
33. Tuist's latest stable CLI is 4.208.0 (2026-09-11), with canaries for 4.209. **[verified]** https://github.com/tuist/tuist/releases
34. Xcode 16 buildable (synchronized) folders record only the folder path in `project.pbxproj`, so adding files no longer edits the project file. **[source claim]** https://pepicrft.me/blog/2024/07/20/how-synchronized-groups-work-at-the-pbxproj-level , https://tuist.dev/blog/2025/03/21/git-conflicts
35. A Swift package cannot produce an iOS app outside Swift Playgrounds: the `iOSApplication` product from `AppleProductTypes` works only in `.swiftpm` playground packages, and Apple's forum error reads "ios app products are only permitted in swift playground packages". **[source claim]** https://developer.apple.com/forums/thread/766123 , https://skyaaron.com/posts/swiftpm-app-projects/ . `swift package init --type` offers no app type. **[local]**

### 3.6 Swift language and concurrency

36. New Xcode 26 app projects default `SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor` and `SWIFT_APPROACHABLE_CONCURRENCY = YES` (which enables `NonisolatedNonsendingByDefault` and `InferIsolatedConformances`); existing projects default to `nonisolated`. Packages get the same behaviour through `swiftSettings`. **[source claim]** https://www.donnywals.com/setting-default-actor-isolation-in-xcode-26/ , https://useyourloaf.com/blog/approachable-concurrency-in-swift-packages/
37. `Observations` (SE-0475, Swift 6.2, iOS 26) is an `AsyncSequence` of transactional snapshots of `@Observable` state; multiple synchronous changes before the next suspension arrive as one value, and every iteration begins with the current value. **[verified]** https://github.com/swiftlang/swift-evolution/blob/main/proposals/0475-observed.md ; behaviour summary **[source claim]** https://useyourloaf.com/blog/swift-observations-asyncsequence-for-state-changes/
38. Swift Testing `-only-testing` identifiers for functions inside a suite may need a doubled pair of parentheses because xcodebuild strips the last pair. No source confirms a fix in Xcode 26 or 27. **[source claim]** https://trinhngocthuyen.com/posts/tech/swift-testing-and-xcodebuild/

### 3.7 Libraries

39. swift-openapi-generator 1.13.1 (2026-09-01): a build plugin plus CLI; OpenAPI 3.0 and 3.1, 3.2 preliminary; generated code needs `swift-openapi-runtime` and a transport such as `swift-openapi-urlsession` (1.3.1); config file `openapi-generator-config.yaml` in the target's source directory with `generate`, `accessModifier`, `namingStrategy`, `filter`; the FAQ says the plugin is recommended and generated code need not be committed, but "if you require to check your generated code into git, you can use the command plugin, or manually invoke the command-line tool"; in Xcode the plugin must be trusted ("Trust & Enable") or the build fails with "OpenAPIGenerator is disabled"; Xcode projects using `package` access need `SWIFT_PACKAGE_NAME`. **[verified]** https://github.com/apple/swift-openapi-generator and its `Documentation.docc` articles; release dates from GitHub API.
40. GRDB.swift 7.11.1 (2026-06-18); Point-Free SQLiteData 1.12.0 (2026-08-31), built on GRDB, with CloudKit sync and sharing. **[verified]** GitHub releases; https://github.com/pointfreeco/sqlite-data
41. SwiftData in iOS 27 adds sectioned queries, `Codable` attributes (not usable in predicates), enum and compound predicates, `ResultsObserver` and `HistoryObserver`. Commentators report that `ModelActor` "continues to sometimes run code on the main thread", no public or shared-database sync, and no clear performance signal. **[verified]** https://developer.apple.com/videos/play/wwdc2026/274/ (title), https://mjtsai.com/blog/2026/06/23/swiftdata-in-appleos-27/ ; the criticisms are **[source claim]**.
42. swift-snapshot-testing 1.19.4 (2026-07-28). **[verified]** GitHub releases (details in report 08).
43. xcbeautify 3.2.1 (2026-04-04) exists as a log formatter; not installed here. **[verified]** GitHub releases.

### 3.8 Platform services in the simulator

44. The simulator can receive real remote notifications from the APNs sandbox on Apple silicon or T2 Macs (since Xcode 14 and macOS 13), with a device token unique to the simulator and Mac pairing. **[source claim]** https://nilcoalescing.com/blog/TestingRemotePushOniOSSimulator/ . Receiving a real token still requires the push entitlement and an App ID, which means a paid team.
45. Background tasks cannot be forced by the system scheduler in the simulator; the known route is pausing in LLDB and calling the private `_simulateLaunchForTaskWithIdentifier:` on `BGTaskScheduler`. **[source claim]** https://developer.apple.com/forums/thread/702402 . This is interactive debugger work, not an automatable gate.
46. Passkeys need the Associated Domains capability and a reachable `apple-app-site-association` file; Apple's CDN caches it for up to 24 hours, and `?mode=developer` on the entitlement bypasses the CDN for development. Reports of `ASAuthorizationErrorDeviceNotConfiguredForPasskeyCreation` on iOS 26 simulators exist. **[source claim]** https://www.corbado.com/blog/test-passkeys-native-ios-android-apps , https://docs.corbado.com/corbado-connect/helpful-guides/ios-testing
47. Free personal teams cannot use Sign in with Apple, push, iCloud, App Groups or Associated Domains. **[source claim]** https://takazudomodular.com/pj/zudo-tauri/docs/mobile/ios-signing-free-team/ . Simulator builds do not require a team for code that uses none of those services. **[opinion, verify on first build]**

### 3.9 Release requirements

48. Since 2026-04-28, uploads to App Store Connect must be built with Xcode 26 or later against the iOS 26 SDK; updated age-rating answers were due 2026-01-31; required-reason API declarations have been enforced since 2024-05-01. No 2027 requirement is posted yet. **[verified]** https://developer.apple.com/news/upcoming-requirements/
49. Privacy manifests (`PrivacyInfo.xcprivacy`) contain `NSPrivacyTracking`, `NSPrivacyTrackingDomains`, `NSPrivacyCollectedDataTypes` and `NSPrivacyAccessedAPITypes`; required-reason categories include file timestamps, system boot time, disk space, active keyboards and user defaults; Xcode can generate an aggregated privacy report from an archive. **[verified]** https://developer.apple.com/documentation/bundleresources/privacy-manifest-files
50. App Privacy answers ask, per data type, whether it is collected (sent off device and kept longer than needed to service the request in real time), linked to identity, and used for tracking; on-device-only processing is not collection; data from third-party SDKs must be disclosed. **[verified]** https://developer.apple.com/app-store/app-privacy-details/
51. Screenshots: 1 to 10 per device class, PNG or JPEG without alpha; iPhone needs 6.9-inch images (accepted portrait sizes 1260×2736, 1290×2796, 1320×2868) or the 6.5-inch set; iPad apps need 13-inch images (2064×2752 or 2048×2732 portrait). **[verified]** https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications
52. TestFlight: up to 100 internal testers without Beta App Review; up to 10,000 external testers, with the first build to an external group reviewed; builds are testable for 90 days; external testing needs a beta description, what to test, and a feedback email. **[verified]** https://developer.apple.com/help/app-store-connect/test-a-beta-version/testflight-overview
53. Upload from the command line: `xcodebuild -exportArchive` with an export options plist whose `destination` is `upload` and `method` is `app-store-connect`. **[source claim]** https://lilting.ch/en/articles/xcode-cli-claude-code-ios-automation ; method names **[local]** per fact 19.

---

## 4. Detailed spec

### 4.1 When the pack loads, and what it produces

The orchestrator loads `references/ios.md` whenever intake finds any of: a `*.xcodeproj`, `*.xcworkspace`, `project.yml`, `Project.swift` (Tuist), a `Package.swift` whose platforms include `.iOS`, or a goal that names iPhone, iPad, iOS, SwiftUI or the App Store. It adds these files to the project's `.drive/` state:

```
.drive/ios/
  toolchain.md        # doctor output: Xcode path and build, Swift, runtimes, chosen UDIDs, MCP status
  devices.json        # role -> {name, udid, runtime} for phone, small-phone, large-phone, tablet
  facts.md            # verified quirks for this project (test-id syntax, schema keys, signing outcome)
.drive/evidence/<run>/ios/
  build.log  build.xcresult  fast.xcresult  ui.xcresult  enumerate-*.json  summary-*.json
  capture/<screen>/<device>-<appearance>-<textsize>-<state>.png (+ .tree.json)
  manifest.json       # git hash, build hash read back from the installed app, UDIDs, backend URL
```

and these repo files for a greenfield app (names generic; adapt the product name):

```
project.yml                      # XcodeGen spec; the .xcodeproj is generated and git-ignored
Configs/Base.xcconfig  Debug.xcconfig  Release.xcconfig
App/                             # thin app shell: @main App, root scene, dependency wiring, Info.plist, assets
AppUITests/                      # XCUITest flows, accessibility audits, launch test
TestPlans/Fast.xctestplan  UI.xctestplan  Live.xctestplan
Packages/                        # one local Swift package, many products
  Package.swift
  Sources/Core  Networking  Persistence  DesignSystem  FeatureX ...  AppFeature
  Tests/CoreTests  NetworkingTests  PersistenceTests  FeatureXTests ...
scripts/ios/doctor.sh  gen.sh  build.sh  test.sh  run.sh  capture.sh  live.sh
openapi/                         # the contract copied from the backend, plus the generator config
PrivacyInfo.xcprivacy            # created at the start, not at release time
```

### 4.2 Toolchain preflight (doctor)

Run once at the start of any iOS work and again whenever a build fails in a way that does not point at source code. The doctor writes `.drive/ios/toolchain.md` and exits non-zero on anything that would make later evidence untrustworthy.

1. Pin the developer directory for every child process: `export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer`, then record `xcodebuild -version` and `swift --version`. Two Xcodes are installed on this Mac; the scripts must never depend on global selection.
2. List runtimes with `xcrun simctl list runtimes -j`. If the project's deployment target is higher than the newest installed runtime, stop and surface one decision to the owner: lower the target or download the runtime with `xcodebuild -downloadPlatform iOS`. Downloading is several gigabytes and needs his yes; do not start it silently, and do not silently lower the target either.
3. Resolve devices by role into `devices.json`. Prefer dedicated devices named `drive-<project>-<role>` created with `xcrun simctl create <name> <device type id> <runtime id>` so agent runs do not fight the owner's own booted simulators. Roles: `phone` (iPhone 17 Pro), `small` (iPhone 17e, or iPhone SE 3rd generation if the design calls for the smallest screen), `large` (iPhone 17 Pro Max, which is also the 6.9-inch screenshot source), `tablet` (iPad Pro 13-inch M5) only if the app supports iPad. When runtimes share an identifier, as the two iOS 26.4 builds do here, record the exact runtime build next to the UDID.
4. Check the Simulator MCP: call `control attach` for the phone UDID, then `control screenshot`. Record `mcp: available` or the exact error. If the error is the `xcode-select` message, write it into `toolchain.md` and tell the owner the command once in the run summary; carry on with `simctl` and XCUITest.
5. Check generators: `xcodegen --version`. If the project uses Tuist, `tuist version`. Record them.
6. Check disk: fail if the volume holding DerivedData has less than 20 GB free, because the resulting failures (codesign errors, simulator boot failures, half-written result bundles) look like code problems and waste hours.

### 4.3 Project setup without the GUI

**Decision table.**

| Situation | Use | Why |
|---|---|---|
| Greenfield app, one developer plus agents | XcodeGen `project.yml` + one local Swift package for all modules; `.xcodeproj` git-ignored | Agents edit YAML and `Package.swift` accurately; generation is idempotent and fast; the spec reads like documentation; XcodeGen is already installed and needs no account or daemon. |
| Greenfield with many app targets, extensions, or a platform team that wants caching | Tuist | Typed Swift manifests, module graph checks, binary caching. Heavier: its own CLI release train (4.208 this week), more moving parts, and it already broke once on the Xcode 27 deployment-target change. Worth it past roughly ten targets, not before. |
| Existing app with a checked-in `.xcodeproj` | Keep it. Convert groups to buildable folders only if the owner agrees, as its own commit. | Converting a working project is a migration, not a setup detail. Buildable folders already remove most `pbxproj` churn when adding files. |
| Existing Tuist or XcodeGen project | Use its generator; never hand-edit the generated project | Hand edits are lost on the next generation and produce "works until regenerate" mirages. |
| "Pure Swift package app" | Not viable for a shippable iOS app | The `iOSApplication` product works only in Swift Playgrounds packages (fact 35). Use packages for modules, not for the app. |

**Why agents do better with generated projects.** `project.pbxproj` is a machine-written object graph keyed by 24-character identifiers. An agent adding a target by editing it must invent identifiers, cross-reference build phases, configuration lists and product references, and keep the file's odd plist dialect valid; one missed reference yields a project that opens but builds the wrong thing, and the diff is unreviewable. With XcodeGen the same change is five lines of YAML and the verifier can read it. With buildable folders plus a local package, most day-to-day work never touches the project spec at all: a new feature is a new directory under `Packages/Sources` and one product line in `Package.swift`.

**Template `project.yml`** (generic names; keys checked against the XcodeGen spec; the signing lines are an opinion to verify on the first build, see below):

```yaml
name: App
options:
  bundleIdPrefix: com.example
  deploymentTarget: { iOS: "26.0" }
  projectFormat: xcode16_0
  createIntermediateGroups: true
configFiles:
  Debug: Configs/Debug.xcconfig
  Release: Configs/Release.xcconfig
packages:
  AppPackages: { path: Packages }
targets:
  App:
    type: application
    platform: iOS
    sources:
      - path: App
        type: syncedFolder
    dependencies:
      - package: AppPackages
        product: AppFeature
    info:
      path: App/Info.plist
      properties:
        UILaunchScreen: {}
        DriveBuildHash: $(DRIVE_BUILD_HASH)
        API_BASE_URL: $(API_BASE_URL)
    settings:
      base:
        PRODUCT_BUNDLE_IDENTIFIER: com.example.app
        ASSETCATALOG_COMPILER_APPICON_NAME: AppIcon
  AppUITests:
    type: bundle.ui-testing
    platform: iOS
    sources: [AppUITests]
    dependencies: [{ target: App }]
schemes:
  App:
    build: { targets: { App: all, AppUITests: [test] } }
    run: { config: Debug }
    test:
      config: Debug
      testPlans:
        - { path: TestPlans/Fast.xctestplan, defaultPlan: true }
        - { path: TestPlans/UI.xctestplan }
        - { path: TestPlans/Live.xctestplan }
    archive: { config: Release }
```

`Configs/Base.xcconfig` (included by Debug and Release):

```
SWIFT_VERSION = 6.0
SWIFT_STRICT_CONCURRENCY = complete
SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor
SWIFT_APPROACHABLE_CONCURRENCY = YES
SWIFT_TREAT_WARNINGS_AS_ERRORS = YES
ENABLE_USER_SCRIPT_SANDBOXING = YES
MARKETING_VERSION = 0.1.0
CURRENT_PROJECT_VERSION = 1
DRIVE_BUILD_HASH = unknown
CODE_SIGN_STYLE = Automatic
DEVELOPMENT_TEAM =
CODE_SIGN_IDENTITY[sdk=iphonesimulator*] = -
```

Unit tests for modules live in the package (`Packages/Tests/*`) and run through the package's own schemes on a simulator destination, so the app project needs only the UI test target. If a test must exercise the assembled app (for example dependency wiring), add a small `AppTests` `bundle.unit-test` target with the app as host.

**Test plans are hand-written JSON.** XcodeGen does not generate them (fact 31). The agent writes `TestPlans/*.xctestplan` directly; the format is plain JSON with `configurations`, `defaultOptions` and `testTargets`. After writing one, the gate is `xcodebuild -showTestPlans -scheme App` followed by an enumeration (4.4) proving the plan selects the intended targets.

**Build stamp, corrected from report 09.** Report 09 proposed putting the short git hash into `CFBundleVersion`. That works for Debug evidence but breaks the release path, because App Store Connect requires `CFBundleVersion` to be period-separated integers. Put the hash in a custom Info.plist key instead (`DriveBuildHash`, set from the `DRIVE_BUILD_HASH` build setting on the command line) and read it back from the installed bundle:

```bash
APP=$(xcrun simctl get_app_container "$UDID" "$BUNDLE" app)
plutil -extract DriveBuildHash raw "$APP/Info.plist"   # must equal git rev-parse --short HEAD
```

**Signing without an account.** Simulator builds of apps that use no restricted capability should build with automatic style, an empty team and ad hoc identity `-` for the simulator SDK. I did not build anything today, so this is a verify-on-first-build item: the doctor's first build records the outcome in `facts.md`, and `codesign -d --entitlements - "$APP"` shows whether entitlements were embedded. Do not reach for `CODE_SIGNING_ALLOWED=NO` by reflex. It speeds up builds, but forum reports say the entitlements file is then not produced (fact search above, source claim), which breaks Keychain access groups and App Groups in the simulator and produces tests that pass for the wrong reason or fail mysteriously.

Capabilities that need a paid team even to exercise in the simulator: Sign in with Apple, real APNs tokens, Associated Domains (passkeys, universal links), App Groups used across processes, iCloud and CloudKit. When the spec includes any of these, the orchestrator surfaces one decision to the owner at the start: the Team ID and the reverse-DNS bundle identifier to register. Until he answers, the agent builds those features behind a protocol with a simulator-safe implementation, marks them `Partial` with the reason "blocked on team", and keeps going on everything else. The agent never signs in to an Apple account, never enters credentials, and never creates App IDs through a browser.

**Schemes and configurations.** Keep two build configurations (Debug, Release) and express environments as build settings plus launch arguments, not as extra configurations. A third "Staging" configuration multiplies every signing, package and cache path and is a common source of "works in Debug only" failures. The backend URL comes from `API_BASE_URL` in the xcconfig with a launch-argument override (`-API_BASE_URL https://…`), which `UserDefaults` picks up automatically; the app reads the override first and the Info.plist value second. One shared scheme for the app, test plans for lanes.

**Generation discipline.** `scripts/ios/gen.sh` runs `xcodegen generate --spec project.yml` and then `xcodebuild -list -json -project App.xcodeproj` to prove the schemes and targets exist. Every script that builds calls `gen.sh` first, so a stale generated project never survives a spec change. `App.xcodeproj` is in `.gitignore`. The Simulator MCP `build` action needs an absolute `project_path`, so generation must happen before any MCP build call too.

### 4.4 The build, run and test loop

Report 08 gives the core `xcodebuild test` and `xcresulttool` commands. This section adds what makes them reliable in an agent loop: fixed paths, the build-once-test-many split, zero-test guards, compile-error extraction, and simulator state control.

**Fixed paths.** Every invocation uses the same four directories, all git-ignored and inside the checkout (so each worktree gets its own):

```bash
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
DD=.build/ios/DerivedData
SPM=.build/ios/SourcePackages
EVID=.drive/evidence/$RUN/ios
UDID=$(jq -r '.phone.udid' .drive/ios/devices.json)
```

**Build once, test many.** Build products for testing a single time per code state, then run each lane without rebuilding. This halves loop time and guarantees every lane tested the same binary.

```bash
scripts/ios/gen.sh
xcodebuild build-for-testing \
  -project App.xcodeproj -scheme App -configuration Debug \
  -destination "id=$UDID" -destination-timeout 120 \
  -derivedDataPath "$DD" -clonedSourcePackagesDirPath "$SPM" \
  -onlyUsePackageVersionsFromResolvedFile \
  -skipPackagePluginValidation -skipMacroValidation \
  -resultBundlePath "$EVID/build.xcresult" \
  DRIVE_BUILD_HASH="$(git rev-parse --short HEAD)" \
  > "$EVID/build.log" 2>&1
```

The two `-skip…Validation` flags are acceptable only because the package list is pinned in `Package.resolved` and reviewed; the flags trust every macro and build plugin in the dependency graph. Adding a package with a macro or plugin is therefore a reviewed change, and the verifier checks `Package.resolved` diffs for new plugin-bearing packages. The MCP `build` action makes the same trust decision implicitly (fact 26).

When the build fails, extract errors from the result bundle rather than scrolling the log: `xcrun xcresulttool get build-results --path "$EVID/build.xcresult" --compact`. Learn the JSON key names once with `--schema`, record them in `.drive/ios/facts.md`, and have the script print only file, line and message. Hand the agent those lines and nothing else; a 40,000-line build log in context is how agents lose the thread.

**Zero-test guard.** Before each lane, enumerate what it will run and fail if the count is zero or does not include the tests the task names:

```bash
xcodebuild test-without-building -project App.xcodeproj -scheme App \
  -testPlan Fast -destination "id=$UDID" -derivedDataPath "$DD" \
  -enumerate-tests -test-enumeration-style flat -test-enumeration-format json \
  -test-enumeration-output-path "$EVID/enumerate-fast.json"
```

Then run the lane with `test-without-building`, the same flags, `-resultBundlePath "$EVID/fast.xcresult"`, and after it `xcrun xcresulttool get test-results summary --path "$EVID/fast.xcresult"`. The script asserts that the executed count in the summary is at least the enumerated count. This also settles the Swift Testing parentheses question per project: enumerate with the filter in both forms, keep whichever selects the test, record it in `facts.md`.

**Lanes.**

| Lane | Plan | What runs | Parallel | Budget |
|---|---|---|---|---|
| fast | `Fast` | package test targets (Swift Testing), in-memory real stores, stubbed network | yes | under 90 s warm |
| ui | `UI` | XCUITest flows with fixture data via launch arguments, accessibility audits, launch test across configurations | no, one device | under 10 min |
| live | `Live` | a few XCUITest flows with `-API_BASE_URL` pointing at the deployed staging backend and a run-scoped test account | no | under 5 min |
| snap | inside `Fast` or `UI` | swift-snapshot-testing on signature screens, pinned device and runtime | no | under 2 min |

Modules with no UIKit or SwiftUI dependency (`Core`, parts of `Networking` and `Persistence`) should also compile for macOS so `swift test --package-path Packages --filter CoreTests` runs in seconds during inner-loop edits. That is a speed convenience, not proof: the gate still runs those tests on the simulator destination, because macOS Foundation and the iOS runtime differ in small ways (file protection, locale data, background execution) and the harness must not be kinder than the target.

**Running and driving the app.**

```bash
xcrun simctl bootstatus "$UDID" -b                 # boots if needed and waits until ready
APP="$DD/Build/Products/Debug-iphonesimulator/App.app"
xcrun simctl install "$UDID" "$APP"
xcrun simctl privacy "$UDID" reset all com.example.app      # start from a known permission state
SIMCTL_CHILD_DRIVE_LOG=1 xcrun simctl launch --terminate-running-process \
  --stdout="$EVID/app.out" --stderr="$EVID/app.err" \
  "$UDID" com.example.app -DriveState loaded -API_BASE_URL "$BASE_URL"
xcrun simctl openurl "$UDID" "exampleapp://item/123"        # deep links
xcrun simctl push "$UDID" com.example.app "$EVID/payload.apns"   # push handling without APNs
xcrun simctl addmedia "$UDID" fixtures/photos/*.heic         # seed the library for PhotosPicker flows
xcrun simctl location "$UDID" set 51.5074,-0.1278
xcrun simctl spawn "$UDID" log stream --style compact \
  --predicate 'subsystem == "com.example.app"' > "$EVID/os.log" &   # app's os.Logger output
xcrun simctl get_app_container "$UDID" com.example.app data  # inspect the sandbox, e.g. the SQLite file
xcrun simctl keychain "$UDID" reset                          # clean auth state between flows
xcrun simctl erase "$UDID"                                   # last resort for a poisoned device (shut it down first)
```

`bootstatus` is present in current `simctl` builds but I did not see it in today's top-level help listing; if it is missing, boot with `simctl boot` and poll `simctl list devices -j` for `Booted`. Record which one works in `facts.md`.

**Privacy grants hide bugs.** Pre-granting photos or location makes flows deterministic, and it also skips the only moment a missing `NS…UsageDescription` key would crash the app. Keep one UI test per protected resource that resets the permission, triggers the real system prompt, and accepts it through an interruption monitor or `springboard` query. That test is the guard for the kindness the grant introduces.

**Simulator MCP usage rules.**

1. Preflight with `attach` then `screenshot` for the target UDID; if either errors, record it and use the `simctl` and XCUITest path. Never report a check as passed when the tool that performs it was unavailable.
2. Always pass `device` as a UDID from `devices.json`, never a name, because names repeat across runtimes.
3. Use MCP `build` only for exploratory work; gates use `scripts/ios/build.sh`, because the script records flags, paths and the result bundle and the MCP build does not produce a result bundle in the evidence folder.
4. After `launch`, read the build hash from the installed Info.plist (4.3) before collecting any evidence.
5. Prefer `inspect` to screenshots for textual and structural assertions: find elements by label or identifier, check `value`, check frames against the 44-point minimum and the safe area. Tap at the centre of a returned frame. Remember that `inspect` omits hidden and off-screen elements and cannot detect occlusion, so "element present" is not "element visible"; pair it with a screenshot for anything that could be covered.
6. Start swipes more than 4 points from any edge unless an edge gesture is intended.
7. For flows that must be repeatable (Live Proof, regression), encode them as XCUITest in the `Live` or `UI` plan rather than as MCP taps. MCP walkthroughs are for discovery and for the reviewer's independent look.

If the owner prefers a second tool, XcodeBuildMCP (fact 29) covers the same ground with a CLI mode; the skill should not install it by default, because it adds telemetry and a daemon, and the scripts above already provide the reproducible path.

**Derived-data hygiene.** Symptoms that mean "clean, do not debug the code": a test runs old behaviour after an edit; `No such module` for a module that exists; a Swift macro or plugin error after a package update; a crash in code that was deleted; `build-for-testing` succeeds and `test-without-building` cannot find the test bundle. The remedy, in order: delete `$DD/Build/Products` and rebuild; delete all of `$DD`; delete `$SPM` and re-resolve with `xcodebuild -resolvePackageDependencies`; `xcrun simctl uninstall` the app; `simctl shutdown` then `simctl erase` the device. Record which step fixed it. The second time the same symptom needs the same clean, treat the clean as a workaround hiding a real cause (commonly a generated file written into sources, a build phase without declared outputs, or two worktrees sharing one DerivedData).

### 4.5 Testing guidance

Report 08 fixes the frameworks (Swift Testing for logic, XCTest for UI, performance and audits), snapshots, the audit test and the offline stub idea. This section adds the pieces an agent needs to write those tests correctly under Swift 6.4, and the shape of a minimal but hard suite.

**Network stubbing that survives parallel Swift Testing.** Swift Testing runs tests in parallel by default, and the classic `URLProtocol` stub with one static handler makes parallel tests read each other's responses. Key handlers by a unique host per test, which the client under test receives as its base URL:

```swift
import Foundation
import Synchronization

final class StubURLProtocol: URLProtocol, @unchecked Sendable {
  typealias Handler = @Sendable (URLRequest) throws -> (HTTPURLResponse, Data)
  private static let handlers = Mutex<[String: Handler]>([:])

  /// Returns a session and a base URL whose host routes only to this handler.
  static func make(_ handler: @escaping Handler) -> (URLSession, URL) {
    let host = "\(UUID().uuidString.lowercased()).stub.invalid"
    handlers.withLock { $0[host] = handler }
    let config = URLSessionConfiguration.ephemeral
    config.protocolClasses = [StubURLProtocol.self]
    return (URLSession(configuration: config), URL(string: "https://\(host)")!)
  }

  override class func canInit(with request: URLRequest) -> Bool { true }
  override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }

  override func startLoading() {
    guard let host = request.url?.host,
          let handler = Self.handlers.withLock({ $0[host] }) else {
      client?.urlProtocol(self, didFailWithError: URLError(.cannotFindHost)); return
    }
    do {
      let (response, data) = try handler(request)
      client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
      client?.urlProtocol(self, didLoad: data)
      client?.urlProtocolDidFinishLoading(self)
    } catch {
      client?.urlProtocol(self, didFailWithError: error)
    }
  }
  override func stopLoading() {}
}
```

Two kindness-ledger entries come with this stub and must be written down. Inside a `URLProtocol`, `request.httpBody` is usually nil because the body arrives as `httpBodyStream`, so request-body assertions must read the stream. And the stub never produces partial reads, slow responses, HTTP/2 resets or TLS failures; claims about timeouts and retries need either a handler that sleeps and throws `URLError(.timedOut)` or a live check. `Mutex` needs iOS 18 or later, which a 26.0 deployment target satisfies.

**Contract fixtures.** Stub responses come from files under `Packages/Tests/Fixtures/api/` that the backend's contract tests validate against the same OpenAPI document (report 08, section 4.3). A handler that returns hand-typed JSON is a mirage source: it encodes the client author's belief about the server.

**Observation-based state tests.** Design view models so that every user intent is an `async` method that returns when the resulting state has settled. Then tests need no observation machinery at all:

```swift
@Suite @MainActor struct ItemListModelTests {
  @Test func showsCachedItemsWhenOffline() async throws {
    let store = try Store.inMemory()                       // real SQLite or SwiftData, in memory
    let (online, base) = StubURLProtocol.make(Fixtures.itemsPage1)
    let model = ItemListModel(api: .init(session: online, baseURL: base), store: store)
    await model.refresh()
    #expect(model.items.count == 20)

    let (offline, base2) = StubURLProtocol.make { _ in throw URLError(.notConnectedToInternet) }
    let reopened = ItemListModel(api: .init(session: offline, baseURL: base2), store: store)
    await reopened.refresh()
    #expect(reopened.items.count == 20)
    #expect(reopened.banner == .offline)
  }
}
```

Use `Observations` only for state changed from outside an intent (a push arrives, a sync engine finishes). Iterate the sequence until a predicate holds and bound the wait with a task-group timeout; Swift Testing's `.timeLimit` works in whole minutes and is a backstop, not a wait mechanism. Because every iteration of an `Observations` sequence starts with the current value (fact 37), assert on the first value that satisfies the predicate, not on the second element. Never use `Task.sleep` to wait for state; that is the most common source of iOS test flakiness in agent-written suites. Inject a clock (`any Clock<Duration>`) into anything with debounce, retry or expiry so tests control time.

**Main-actor defaults in tests.** With `SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor` on the app and packages, view models are main-actor isolated, and test suites that touch them should be annotated `@MainActor` explicitly rather than relying on the test target's defaults, which I could not verify for package test targets today. Pure logic types that are `nonisolated` and `Sendable` get parallel tests without annotation. Record in `facts.md` what the package's test target isolation actually is after the first compile.

**XCUITest flows.** Rules the pack enforces:

- Every interactive element the tests touch gets an `accessibilityIdentifier` from a shared enum in `DesignSystem` or a small `AccessibilityIDs` file used by both app and UI tests; tests never query by visible English text except to assert copy.
- The app reads `-DriveState <name>` and `-DriveNetwork <mode>` launch arguments in Debug (report 09) to select fixture repositories; UI tests pass them through `app.launchArguments`. The Live plan passes `-API_BASE_URL` and a run-scoped account instead.
- Waits use `waitForExistence(timeout:)` or expectations on element predicates; no `sleep`.
- Each flow test ends by calling `performAccessibilityAudit` on the last screen (report 08 has the pattern) and attaching `XCUIScreen.main.screenshot()` with `lifetime = .keepAlways` so the reviewer can read it from the result bundle.
- Set the Xcode 27 test-plan crash severity for UI tests to "failure" (the default) or stricter; never "warning".
- One launch test per app uses `runsForEachTargetApplicationUIConfiguration` to cover appearance and orientation; one `XCUIVoiceOverService` test walks the primary flow.

**Dynamic Type and dark mode.** UI tests can set `app.launchArguments += ["-UIPreferredContentSizeCategoryName", "UICTContentSizeCategoryAccessibilityXXXL"]` for a launch at the largest size; this is a long-standing launch-argument convention I did not re-verify today, so the first UI test that uses it asserts that a known label's frame grew. For capture, `simctl ui content_size` and `simctl ui appearance` (fact 25) are verified. Snapshot tests carry the traits explicitly (report 08).

**What a minimal but hard suite looks like for a mid-sized app** (roughly 15 screens, 30 endpoints, local persistence, sync, auth). The number is small on purpose; each test names the claim it tries to refute.

| Layer | Count | What each proves or tries to break |
|---|---|---|
| Core logic (Swift Testing, parameterized) | 25 to 40 | Domain rules with boundary values: empty, one, maximum, invalid, time zones and locales where dates or money appear. |
| Networking | 1 per endpoint family, plus 6 | Decoding every contract fixture; unknown enum values and extra fields tolerated; 401 triggers one refresh then sign-out; 429 and 5xx back off; offline surfaces a typed error; request encoding matches the contract. |
| Persistence | 8 to 12 | Migrations from every shipped schema version using stored fixture databases; uniqueness and cascade rules; large batch writes; concurrent writes from a background actor; corrupted or missing store recovery. |
| Sync engine | 8 to 10 | Outbox replay is idempotent; conflict policy; partial failure mid-batch; cursor persistence across relaunch; clock skew; deletion propagation both ways. |
| View models | 1 to 3 per screen | Loading, loaded, empty, error, offline states reachable and correct; intents change state as the spec says. |
| XCUITest flows | 5 to 8 | Onboarding and sign-in, the two primary jobs end to end, permission prompt per resource, deep link entry, sign-out clears data. Each ends with an accessibility audit. |
| Snapshots | 3 to 5 screens | Signature screens only, light and dark, default and AX5 text, pinned simulator. |
| Launch and VoiceOver | 2 | Every configuration launches; the primary flow is operable under VoiceOver. |
| Live | 2 to 3 | Against staging: sign-in with a test account, one read showing server data, one write read back from the backend. |

The verifier's manual mutation pass (report 08) applies: for the five riskiest claims, break the production line, run the named test, expect red.

### 4.6 Architecture guidance for any such app

These are defaults the skill gives an agent building a new app. Each is overridable by the spec with a logged reason. Items marked "verify" must be checked against the project's actual deployment target and SDK at design time and the result written into `DECISIONS.md`.

1. **Deployment target.** Build with the newest installed SDK (iOS 27 with Xcode 27) and target iOS 26.0 for a greenfield consumer app in late 2026, which gives `Observations`, the Liquid Glass APIs and a large installed base. Choose 27 only if the spec needs a 27-only API; choose lower only with evidence about the audience. Verify against the installed runtimes (4.2) so tests can run at the minimum version.
2. **UI and state.** SwiftUI app lifecycle (scene-based by construction, which the iOS 27 SDK requires). `@Observable` models owned by the feature's root view through `@State`; no `ObservableObject` or Combine in new code. With the Xcode 27 `@State` macro (fact 14), do not both default-initialize and assign in `init`. Navigation through `NavigationStack` with a typed route enum per feature, and a pure `DeepLink` parser with its own tests.
3. **Concurrency.** Swift 6 language mode, strict concurrency complete, main-actor default isolation, approachable concurrency on. Work that must leave the main actor (image processing, Vision, bulk decoding, database batches) is marked `@concurrent` or lives in an actor, explicitly. Banned without a comment that names the invariant and a test that exercises it: `@unchecked Sendable`, `nonisolated(unsafe)`, `MainActor.assumeIsolated`, `@preconcurrency import` of first-party modules, `Task.detached`. The stub in 4.5 is the kind of justified exception the rule allows: a `Mutex` guards the only mutable state.
4. **Modules.** One local package, many products: `Core` (models and rules, no UI), `Networking` (generated client plus auth middleware), `Persistence`, `Sync`, `DesignSystem` (tokens, components, accessibility identifiers), one product per feature, and `AppFeature` that composes them. Features depend on `Core`, `DesignSystem` and protocols, never on each other. The app target only wires dependencies. This gives fast incremental builds, enforced boundaries, and small test targets that agents can run in isolation.
5. **Dependencies and injection.** A plain `struct AppDependencies` built in the app target and passed through the SwiftUI environment with `@Entry`; features see protocols or closure structs. Do not store class instances as `@Entry` defaults (Xcode 27 now warns, fact 14 page). No third-party DI framework.
6. **Networking from a contract.** When the backend publishes an OpenAPI document (a Cloudflare Worker using Hono with Zod-OpenAPI, or any framework that emits one), use swift-openapi-generator with `swift-openapi-urlsession`. Generate with the CLI or command plugin into `Packages/Sources/Networking/Generated/` and commit the output, with a fast-lane test that regenerates into a temp directory and diffs. Reasons: agents and reviewers read committed code but not files hidden in DerivedData; the build plugin needs a trust prompt or `-skipPackagePluginValidation`; and a committed diff makes contract drift visible in review. Wrap the generated `Client` in a small hand-written facade so features never import generated types directly. Hand-written `Codable` is acceptable when there are fewer than about ten endpoints and no machine-readable contract, and then the contract fixtures (4.5) are mandatory. Verify at project time: the backend's OpenAPI version (3.1 fully supported, 3.2 preliminary) and whether the generator handles its `oneOf` and discriminator usage.
7. **Auth.** Sign in with Apple as the primary path when the app offers any third-party login (App Review has long required an equivalent privacy-preserving option; verify the current guideline wording at release time), with the backend verifying Apple's identity token and issuing its own session tokens. Passkeys as the account credential where the backend supports WebAuthn: requires Associated Domains and a served AASA file with `?mode=developer` during development. Tokens live in the Keychain with an access group only if an extension needs them. An in-app account deletion path is required for apps with account creation (long-standing guideline; verify wording at release). Simulator reality: both Sign in with Apple and passkeys need a team; passkeys have been unreliable on iOS 26 simulators (fact 46), so the Live plan uses a backend test-account endpoint enabled only in staging, and real Apple and passkey sign-in are listed as device-only checks.
8. **Photos and Vision.** Use `PhotosPicker` from PhotosUI, which runs out of process and does not need photo-library permission for picking; request `photos` access only for features that read the library directly. Camera capture needs `NSCameraUsageDescription` and cannot run in the simulator, so camera flows are device-only and the simulator path substitutes a picker. Run Vision requests off the main actor, downscale inputs first, and treat each request's availability as a runtime question: some requests that rely on the Neural Engine behave differently or fail in the simulator. Verify each Vision request the spec uses in the simulator in the first week and record results in `facts.md`; design a fallback (server-side processing or a plain crop) for any that fail there, because otherwise the UI lane cannot cover the feature.
9. **Persistence.** For an app whose truth lives on its own backend and which needs offline reads and queued writes, use GRDB 7 (or SQLiteData if CloudKit sync is wanted instead of a custom backend): explicit schema and migrations, real SQLite in tests via an in-memory database so the harness is not kinder than production, value-type records that are `Sendable`, and observation of queries. Use SwiftData when the data is a simple local model with light relationships, the app is iOS 26 or later, and nobody needs hand-written SQL or precise concurrency control; test it with an in-memory `ModelConfiguration`, which is still the real store. The iOS 27 additions (sectioned queries, `Codable` attributes, `ResultsObserver`) close some gaps, but the reported `ModelActor` threading issues and the absence of shared-database sync (fact 41) make it the riskier choice for sync-heavy apps. Whichever is chosen, keep persistence behind the `Persistence` module so the other modules never import GRDB or SwiftData.
10. **Offline-first sync.** Local database is the UI's source of truth. Writes go to an outbox table with a client-generated idempotency key, are applied optimistically, and are replayed in order by a `Sync` actor on app foreground, on connectivity regained, after a push, and on a manual refresh. Pulls use a server cursor stored locally. Conflict policy is decided in the spec per entity (server wins, last writer wins per field, or merge) and has its own tests. The backend must accept the idempotency key and return the cursor; that is a cross-team contract item for the backend design.
11. **Push.** Register for remote notifications after an in-context explanation, send the device token to the backend, and let the backend talk to APNs with token-based authentication (a `.p8` key the owner stores as a backend secret). Use `simctl push` with payload files for handling tests (fact 23); use the APNs sandbox to a simulator for one Live check once a team exists (fact 44). Notification service extensions are separate targets and need their own tests.
12. **Background work.** Use SwiftUI's `.backgroundTask(.appRefresh(...))` with identifiers listed under `BGTaskSchedulerPermittedIdentifiers`. Design so that nothing correct depends on a background run happening: the same sync runs on foreground. Background scheduling cannot be driven by automation in the simulator (fact 45), so the sync logic is tested directly and background execution is a device-only observation. This is the iOS form of the owner's rule against waiting on a scheduler.
13. **Configuration and secrets.** No secrets in the app bundle. Base URLs through xcconfig and launch arguments. Feature flags from the backend with local defaults.
14. **Observability.** `os.Logger` with the bundle identifier as subsystem and one category per module, so `simctl spawn log stream` (4.4) gives agents a filtered log; MetricKit subscriber for crashes and hangs in production builds.
15. **Localization.** String Catalogs (`.xcstrings`) from the first commit, even for one language, so copy is reviewable in one file and adding languages is not a refactor.

### 4.7 Design quality on iOS

Report 09 owns the design contract format, tokens file, capture matrix and vision rubric. The iOS additions are what the contract must decide for this platform and how tokens become code.

**What an iOS `DESIGN.md` must capture beyond report 09's template.**

1. Navigation model: tab bar (and which three to five tabs), stack depth per tab, what is modal (sheets with which detents, full-screen covers), and where search lives. iPad: sidebar or tabs, and what happens when an iPad window is resized (iOS 27 changed resize behaviour for full-screen and iPhone-only apps on iPad; fact 13 page).
2. Liquid Glass stance: system bars, tab bars and controls use the system material; custom glass is limited to named places; content never sits under glass without a contrast check. Assume the compatibility opt-out is unavailable (fact 15).
3. Type: text styles only (`.largeTitle` through `.caption2`), custom fonts registered with `relativeTo:` so Dynamic Type scales them; which screens must stay usable at AX5 and how layouts stack horizontally adjacent content at large sizes.
4. Colour: semantic system colours as the base, brand colours as named assets with light, dark and increased-contrast variants; text-over-image rules.
5. Symbols and imagery: SF Symbols with rendering mode and weight rules; image aspect ratios and placeholders.
6. Touch targets and spacing: 44-point minimum, spacing scale, safe-area behaviour, keyboard avoidance.
7. States for every screen: loading, empty, error, offline, partial content, permission denied.
8. Permission priming: a pre-prompt screen before each system prompt, with copy that matches the Info.plist usage string.
9. Motion and haptics: which transitions, what Reduce Motion replaces them with, which actions get haptic feedback.
10. App icon (one Icon Composer `.icon`, fact 16) and launch screen (required, fact 13).

**Encoding tokens in code.** `design/tokens.json` (report 09) is the single source. A script in `scripts/ios/tokens.sh` generates `Packages/Sources/DesignSystem/Generated/`: a colour asset catalog with one `.colorset` per token carrying any, dark and high-contrast appearances; `Color` and `ShapeStyle` static members that reference those assets; a `Spacing` enum; `Font` helpers that map token roles to text styles or to custom fonts with `relativeTo:`; corner radii. Generated code is committed, and a fast-lane test regenerates and diffs. A lint in the fast lane fails the build on literals outside `DesignSystem`: `Color(red:`, `Color(#colorLiteral`, `UIColor(red:`, `.font(.system(size:`, hard-coded padding numbers above a small threshold, and hex strings. Sonnet at low effort can run and fix this lint; the rule itself is mechanical.

**Multi-device vision checks.** Use report 09's matrix and rubric, with devices taken from `devices.json` roles: `phone` for everything, `small` and `large` for primary screens, `tablet` when supported. Each capture's manifest row carries the UDID, runtime build, appearance, content size, state, build hash read from the installed app, and data source (`fixture` or the backend URL). The reviewer rejects any image whose manifest row is incomplete. Run the capture with `status_bar override` set and cleared afterwards, and restore appearance and content size, because the next agent's screenshots otherwise inherit AX5 and dark mode.

### 4.8 Release path (later phase)

Release is a separate phase the orchestrator enters only when the spec says so. Most of it needs the owner's accounts, so the skill prepares everything that does not and surfaces the remainder as a single, complete list once.

**Prepared by agents from the start (not at release time):**

- `PrivacyInfo.xcprivacy` in the app target, updated whenever code starts using a required-reason API. `UserDefaults` is one of the categories (fact 49), so almost every app needs an entry. A fast-lane check greps for the API families (`UserDefaults`, file timestamp attributes, `systemUptime`, disk-space resource keys) and fails if the manifest lacks the category.
- `docs/app-privacy.md`: a data inventory table (data type, collected yes or no under Apple's definition, linked to identity, used for tracking, purpose, retention, which SDK) built from the spec and the backend design. App Privacy answers in App Store Connect are then transcribed, not invented at the last minute.
- Info.plist usage strings for every protected resource, each tested by the real-prompt UI test (4.4).
- `ITSAppUsesNonExemptEncryption` decided and set (typically `NO` for apps that only use standard HTTPS; verify against Apple's export-compliance guidance at release).
- Icon, launch screen, display name, `MARKETING_VERSION`; `CURRENT_PROJECT_VERSION` as an integer that the release script increments.
- Screenshot capture recipe: `large` role device (6.9-inch), `tablet` role if iPad is supported, status bar at 9:41, real-looking seeded data, exported without alpha (for example `sips -s format jpeg`), and dimensions checked against fact 51 before anything is handed over.

**Needs the owner, surfaced as one list:** paid team and Team ID; bundle identifier registration; App Store Connect app record; an App Store Connect API key file placed by him at a path the scripts read (the agent never types or pastes keys); age rating answers; pricing and availability; the App Privacy form submission; export compliance confirmation; TestFlight external test information.

**Commands once those exist:**

```bash
xcodebuild archive -project App.xcodeproj -scheme App -configuration Release \
  -destination 'generic/platform=iOS' -archivePath "$EVID/App.xcarchive" \
  -derivedDataPath "$DD" -allowProvisioningUpdates \
  -authenticationKeyPath "$ASC_KEY_PATH" -authenticationKeyID "$ASC_KEY_ID" \
  -authenticationKeyIssuerID "$ASC_ISSUER_ID" \
  CURRENT_PROJECT_VERSION="$BUILD_NUMBER" DRIVE_BUILD_HASH="$(git rev-parse --short HEAD)"
xcodebuild -exportArchive -archivePath "$EVID/App.xcarchive" \
  -exportOptionsPlist Configs/ExportOptions.plist -exportPath "$EVID/export" \
  -allowProvisioningUpdates -authenticationKeyPath "$ASC_KEY_PATH" \
  -authenticationKeyID "$ASC_KEY_ID" -authenticationKeyIssuerID "$ASC_ISSUER_ID"
```

with `ExportOptions.plist` setting `method` to `app-store-connect` and `destination` to `upload`. Forum reports say API-key authentication has not always worked for the upload destination (source claim in 3.9 search results); if it fails, the fallback is the Transporter app, which is the owner's action.

**Status ladder mapping.** An uploaded build that processed in App Store Connect proves "archives, signs and uploads", nothing about behaviour. Internal TestFlight installed on a physical device by the owner, with the device-only checks from 4.6 performed, is the first point where the device-only features can move past `Partial`. I would call that `Operational` for the app layer only when the backend it talks to is also operational. Publishing to the public App Store is an irreversible public action and always needs the owner's explicit yes.

### 4.9 Gates

**iOS Local Proof** requires all of the following in one evidence folder for one git hash:

1. `doctor` passed; `toolchain.md` names the Xcode build, runtime build and UDIDs used.
2. `gen.sh` regenerated the project and `xcodebuild -list` shows the expected schemes.
3. `build-for-testing` succeeded with warnings treated as errors in first-party modules.
4. Fast lane: enumerated count greater than zero, executed count equal to enumerated, zero failures, no skipped test without a quarantine row.
5. UI lane: same count checks; every screen touched has an accessibility audit with no unexplained ignores.
6. Snapshot tests passed on the recorded device and runtime.
7. The generated-code drift checks (OpenAPI client, tokens) passed.
8. The privacy-manifest check and usage-string prompt tests passed.
9. The independent verifier's mutation pass turned the named tests red.

**iOS Live Proof** additionally requires:

1. The backend is deployed and its URL and version are recorded (report 17's process).
2. The HEAD build is installed on the recorded UDID and `DriveBuildHash` read from the installed bundle equals HEAD.
3. The Live plan passed against that URL with a run-scoped test account.
4. For each primary screen, an accessibility-tree read (MCP `inspect` or XCUITest element values) shows a server-sourced value, and the same value is read back from the backend by `curl` or a database query and saved beside it.
5. The capture matrix for primary screens was produced against live data and graded by the UI reviewer from report 09 with a pass decision.
6. `STATUS.md` lists every device-only or team-blocked capability as not proven, by name.

---

## 5. Conditionals by project shape

**Greenfield app with a Cloudflare backend (the illustrative shape).** Everything in section 4 applies. The skill would instruct agents to produce, in order: the doctor output and device roles; `DECISIONS.md` entries for deployment target, persistence choice, auth methods and whether a team exists; `project.yml`, xcconfigs, the local package skeleton, test plans and the scripts; the OpenAPI contract handshake with the backend design (the backend emits the document; the app generates from a copy in `openapi/` and the backend's CI validates app fixtures against it); tokens generation and the literal lint; the state harness and build stamp; then features, each with its claim table and tests. For a wardrobe-style app, the design phase would flag photography-heavy screens, so text-over-image contrast, Vision request availability in the simulator, and PhotosPicker seeding with `simctl addmedia` become early verification items rather than late surprises. Live Proof waits for a staging backend and a test-account endpoint.

**Deep bug hunt in an existing iOS app.** Skip project setup and architecture. Run the doctor, then reproduce first: write a failing Swift Testing or XCUITest case, or, for a crash, collect the crash log from `~/Library/Logs/DiagnosticReports` or the simulator's `simctl diagnose` bundle and symbolicate against the build's dSYM in DerivedData. Data races: rebuild with `-enableThreadSanitizer YES` and run the reproducing test with `-test-iterations 50 -run-tests-until-failure`. Hangs and main-thread stalls: record with `xcrun xctrace record --template 'Time Profiler'` against the simulator app process (verify the template name with `xctrace list templates`). Concurrency bugs that appeared after moving to Swift 6 mode usually live at an `@unchecked Sendable` or `assumeIsolated` site; grep those first. The fix is proven by the reproducing test turning green and staying green over repeated runs.

**Feature on an existing iOS product.** Detect the project format and obey it: no conversion to XcodeGen, no new package structure unless the existing code already uses packages. Read existing conventions for state (it may be `ObservableObject`, TCA, or UIKit) and follow them unless the feature spec explicitly includes a migration. Add tests in the existing test targets and test plans; if the project has none, add a Fast plan and a UI plan without restructuring. Capture before-and-after screenshots of adjacent screens so the reviewer can check for regressions the feature caused.

**Migration or consolidation.** Common iOS migrations: CocoaPods or Carthage to SwiftPM, `ObservableObject` to Observation, Core Data to SwiftData or GRDB, Swift 5 language mode to Swift 6, UIKit screens to SwiftUI, raising the deployment target (now forced to at least 15 by Xcode 27). Pin behaviour first with UI flows and snapshots of the affected screens on the old code, then migrate one module at a time with the lanes green between steps. For Swift 6 mode, flip `SWIFT_STRICT_CONCURRENCY` to `complete` in Swift 5 mode first, fix warnings module by module from the leaves up, then flip the language mode. For persistence migrations, ship a migration test that opens a real database file produced by the previous app version.

**Research plus website.** The iOS pack is dormant unless the website presents an existing app; then it contributes only the screenshot capture recipe (4.8) for marketing images, with seeded, non-personal data.

**Other shapes that matter.** A Swift package or SDK: no app project; test with `swift test` on macOS and `xcodebuild test -scheme <Package> -destination "id=$UDID"` from the package directory for iOS-specific code; add a privacy manifest if the SDK uses required-reason APIs. App extensions (widgets, share, notification service): each is a target with its own Info.plist, entitlements and memory limits; widgets get timeline tests in Swift Testing and snapshot tests of each family. An iPad-first or Mac Catalyst app: the `tablet` role becomes primary and window resizing enters the capture matrix. A watch companion: out of scope for this pack beyond noting that watch simulators pair with phones (`simctl pair`) and that the lanes double.

**Conditionals to write into the skill.**

- If the spec needs Sign in with Apple, push, passkeys, App Groups or iCloud, ask the owner once for the team and bundle identifier, and until then mark those features `Partial (blocked on team)`.
- If the backend publishes OpenAPI, generate the client; otherwise require contract fixtures validated by the backend's tests.
- If the app uses the camera, background tasks, passkeys or real APNs, list them as device-only in `STATUS.md` from day one.
- If more than one agent runs iOS lanes at once, give each its own device clone and DerivedData path, and serialize UI lanes per device.
- If the Simulator MCP preflight fails, use `simctl` plus XCUITest and say so in every evidence manifest.
- If the deployment target exceeds the newest installed runtime, stop and ask once: lower the target or download the runtime.
- If a Swift package with macros or build plugins is added, the verifier reviews the `Package.resolved` diff before builds continue with validation skipped.

---

## 6. Model and effort assignment

| Role | Model and effort | Tools | Isolation | Notes |
|---|---|---|---|---|
| iOS architect (design phase) | `fable`, high, or `opus` high when the orchestrator is busy | Read, Grep, WebSearch, WebFetch, Bash (read-only commands) | none | Writes the iOS sections of the architecture doc and `DECISIONS.md`: deployment target, persistence, auth, modules, contract. Judgment-heavy and cheap in tokens. |
| Project scaffolder | `sonnet`, medium | Read, Write, Edit, Bash | none (runs before parallel work) | Writes `project.yml`, xcconfigs, package skeleton, test plans, scripts from the templates; must get `gen.sh` and an empty build green. |
| Feature maker | `opus`, high for features with state, sync, auth or concurrency; `sonnet`, medium for presentational screens with a finished design | Read, Write, Edit, Bash, Simulator MCP `build` and `control` | worktree when parallel, with its own `DD` and device clone | Must name claims, write tests first, and run the fast lane before returning. |
| Concurrency fixer | `opus`, high | Read, Edit, Bash | same as the maker it serves | Swift 6 isolation and Sendable errors. Forbidden to add escape hatches without the justification comment and test. |
| iOS runner | `sonnet`, low | Bash, Read, Grep, Glob, Simulator MCP | none | Predefined agent below. Runs scripts, parses result bundles, returns a short structured report so logs never enter the orchestrator's context. |
| Build-failure classifier | `sonnet`, low | Read | none | Given extracted errors, classifies as code, stale derived data, package resolution, signing, destination, disk, or toolchain, and names the first remedy. Can be folded into the runner. |
| Token and lint fixer | `sonnet`, low | Read, Edit, Bash | none | Mechanical. |
| Independent verifier | `opus`, high | as in report 08 plus the scripts here | read-only on sources | Report 08's `drive-verifier`; add the iOS gate checklist from 4.9 to its inputs. |
| UI reviewer | as in report 09 | as in report 09 | none | Uses `scripts/ios/capture.sh` and reads manifests. |

**Predefined subagent: `ios-runner`.** It earns a file in `~/.claude/agents/` because iOS commands are long, easy to get subtly wrong, and produce enormous output; one agent that always runs them the same way and returns a compact verdict protects both correctness and the orchestrator's context.

```markdown
---
name: ios-runner
description: Runs iOS build, test, launch and capture scripts for a project and returns a compact structured result. Use whenever an iOS build, test lane, simulator launch or screenshot capture is needed; never to edit source code.
model: sonnet
effort: low
tools: Bash, Read, Grep, Glob, mcp__Claude_Code_iOS_Simulator__build, mcp__Claude_Code_iOS_Simulator__control
color: blue
---

You run iOS tooling and report facts. You never edit source, project, test or script files.

Inputs you are given: the repository path, the run id, and the action (doctor, gen, build, test <lane>, run <state>, capture <screens>, live).

Procedure:
1. Read .drive/ios/toolchain.md, .drive/ios/devices.json and .drive/ios/facts.md. If toolchain.md is missing or older than the last Xcode change, run scripts/ios/doctor.sh first.
2. Run the matching script from scripts/ios/. Do not type xcodebuild or simctl commands from memory when a script exists. If no script exists for the action, say so and stop.
3. Always export DEVELOPER_DIR as recorded in toolchain.md. Always address simulators by UDID from devices.json. Never use the word booted as a device argument.
4. On build failure, extract errors from the result bundle with xcresulttool and return at most 30 lines of file:line: message. Classify the failure as one of: code, stale-derived-data, package-resolution, signing, destination, disk, toolchain. For stale-derived-data, apply the next clean step from references/ios.md once, rerun, and report which step you applied.
5. On test runs, report enumerated count, executed count, failed tests with their first failure message, and skipped tests. If executed is zero or less than enumerated, the result is FAIL regardless of exit code.
6. Before any capture or live action, read DriveBuildHash from the installed app's Info.plist and compare it with git rev-parse --short HEAD. On mismatch, report FAIL: wrong build.
7. If a Simulator MCP call errors, record the exact message, continue with simctl or XCUITest, and include "mcp unavailable: <message>" in the result.

Return exactly this shape:
RESULT: PASS | FAIL
ACTION: <action>
BUILD: <git hash> installed=<hash or n/a> xcode=<build> runtime=<build> udid=<udid>
COUNTS: enumerated=<n> executed=<n> failed=<n> skipped=<n>
ERRORS: <up to 30 lines or none>
CLASSIFICATION: <class or none>
EVIDENCE: <paths under .drive/evidence/<run>/ios/>
NOTES: <tool fallbacks, cleans applied, anything surprising>
```

No other predefined iOS agent is needed. The makers are ordinary Agent calls with the pack text in their prompt, and the verifier and reviewer already exist in reports 08 and 09.

---

## 7. Failure modes and anti-patterns

Each entry names the failure, how it shows up, how it becomes a mirage, and what the skill does about it.

1. **Stale derived data.** The test passes against yesterday's binary, or a deleted type still links. Mirage: green lanes on code that no longer exists. Prevention: per-checkout `-derivedDataPath`, build-once-test-many on the same products, the ordered clean ladder in 4.4, and the rule that the second identical clean means the diagnosis is wrong.
2. **Unbooted or wrong-state simulator.** `xcodebuild` waits, times out, or boots a different device; the MCP returns errors that agents misread as app crashes. Prevention: doctor boots and waits; `-destination-timeout`; device roles by UDID; dedicated `drive-` devices so the owner's sessions do not collide.
3. **Wrong destination.** `name=iPhone 17 Pro` matches devices on two runtimes, or `OS=26.4` matches two runtime builds (fact 3), or `generic/platform=iOS Simulator` builds without running. Mirage: evidence from a different OS than recorded. Prevention: `id=<UDID>` only, runtime build recorded in the manifest.
4. **Two Xcodes.** A script inherits a different `xcode-select` or `PATH`, builds with Xcode 26.6, and results differ. Prevention: `DEVELOPER_DIR` in every script, Xcode build recorded in every evidence manifest.
5. **Signing.** An agent adds a capability, the simulator build still works, and the feature is reported done although it can never work without a team; or an agent "fixes" slow builds with `CODE_SIGNING_ALLOWED=NO` and silently loses entitlements. Prevention: the team decision surfaced once; capabilities list in `STATUS.md` with team-blocked status; the entitlements check after the first build.
6. **Previews mistaken for tests.** The agent reports that the screen "renders correctly" because a `#Preview` compiled, or uses Xcode's `RenderPreview` output as evidence. Previews use preview data, skip the app's dependency wiring, and run in a different host. Prevention: previews are a design convenience only; evidence is captured from the installed app on a named UDID with the build hash checked.
7. **Async test flakiness.** `Task.sleep` waits, shared static stubs under parallel Swift Testing, `Observations` assertions on the wrong element, UI tests racing animations. Mirage: a quarantined test hides a real race. Prevention: async intents that return on settled state, per-host stubs, injected clocks, `waitForExistence`, report 08's flake policy, and Thread Sanitizer runs on any test that flaked twice.
8. **Swift 6 strict-concurrency errors "fixed" with escape hatches.** `@unchecked Sendable`, `nonisolated(unsafe)`, `assumeIsolated` or `@preconcurrency` appear in a diff to make the compiler quiet. Mirage: a clean build that crashes at runtime or races. Prevention: grep gate in the verifier; each occurrence needs an invariant comment and a test; concurrency fixes go to `opus`.
9. **Missing Info.plist usage strings.** Pre-granted privacy in the simulator hides the missing key; the app crashes on a real device at the first prompt. Prevention: the real-prompt UI test per resource, and a fast-lane check that every framework usage (camera, photos write, location, microphone, contacts) has its key.
10. **Screenshots of the wrong simulator or wrong build.** `simctl io booted` picks the iPad; the maker's screenshot predates the fix; the app on screen is using fixtures while the manifest says live. Prevention: UDID-only capture, `DriveBuildHash` readback, data source label in each manifest row, reviewer captures its own images.
11. **Zero tests executed.** A filter with the wrong parentheses, a test plan that omits a target, or a scheme without the test target runs nothing and exits 0. Prevention: enumerate before running, compare executed to enumerated, fail on zero.
12. **Package plugin and macro trust.** Headless builds fail with "is disabled" and the agent adds validation-skipping flags plus a new package in one change, trusting unknown code. Prevention: skip flags live only in scripts, and new plugin- or macro-bearing packages are a reviewed decision recorded in `DECISIONS.md`.
13. **Generated project drift.** Someone edits `App.xcodeproj` directly (an agent following an Xcode tutorial); the next `gen.sh` erases it. Prevention: project git-ignored, every script regenerates, and the verifier treats any instruction to "open Xcode and change a setting" as a spec change to `project.yml`.
14. **Simulator-only proof for device-only features.** Camera, background refresh, passkeys and real push are marked done after a simulator run that could not exercise them. Prevention: the device-only list in `STATUS.md`, which caps those rows at `Partial` until a device check is recorded.
15. **Deployment target below the SDK floor.** A package declares iOS 13 and Xcode 27 refuses to build it (fact 7), and the agent patches the package checkout. Prevention: bump or replace the dependency, never edit files under the package cache; record in `DECISIONS.md`.
16. **Disk exhaustion.** DerivedData and simulator data fill the volume and produce codesign, install and result-bundle errors. Prevention: the doctor's free-space check, and pruning of old `.build/ios` directories in finished worktrees as part of merge cleanup.
17. **Snapshot baselines recorded on the wrong runtime.** Baselines from iOS 26.4 fail on 27 and are re-recorded in bulk without review. Prevention: report 08's rule of deliberate re-recording in one commit naming the runtime, plus the reviewer looking at the diff images.
18. **Cloud scheduling of iOS work.** A routine or cloud agent is asked to run iOS tests; it cannot, and its report says nothing failed. Prevention: the pack states that iOS evidence is produced only on a Mac with Xcode, and the verifier rejects evidence without an Xcode build number.
19. **MCP silently unavailable.** Covered in report 09; restated because it is the current state of this Mac. Prevention: preflight, fallback, and the manifest note.

---

## 8. Open questions and trade-offs

1. **XcodeGen or Tuist for greenfield.** XcodeGen is simpler, installed, and adequate for an app with a handful of targets; Tuist gives caching and graph checks and costs a second release train and more breakage surface. Recommendation: XcodeGen, revisit past ten targets or when build times exceed five minutes clean.
2. **Commit the generated `.xcodeproj` or not.** Ignoring it keeps diffs clean and prevents hand edits, but anyone opening the repo in Xcode must run `gen.sh` first, and the MCP `build` needs the file to exist. Recommendation: ignore it; the scripts and a one-line README note cover the owner's occasional GUI use.
3. **Commit generated OpenAPI code or use the build plugin.** Committing adds churn and a drift check; the plugin hides code from agents and needs trust. Recommendation: commit, with the regenerate-and-diff test.
4. **SwiftData or GRDB.** SwiftData is first-party and improving; GRDB is explicit, testable and mature. Recommendation: GRDB (or SQLiteData for CloudKit) for sync-heavy apps with their own backend, SwiftData for simple local models; the architect records the choice with the reasons.
5. **The Simulator MCP.** It is the better driver when it works, and it does not work here today. Recommendation: the owner runs `sudo xcode-select -s /Applications/Xcode.app/Contents/Developer` once; the skill keeps the `simctl` fallback permanently.
6. **iOS 27 runtime.** Not installed, and downloading it is the owner's decision. Recommendation: target iOS 26.0 and test on the installed 26.4 runtime now; add a 27 runtime lane when he approves the download, and run the Live plan on both before release.
7. **Swift Testing `-only-testing` syntax on Xcode 27.** Unverified, because verifying needs a project. Recommendation: the enumeration step settles it per project and records the result.
8. **Simulator signing defaults.** My template's `CODE_SIGN_IDENTITY[sdk=iphonesimulator*] = -` with an empty team is a reasoned default, not a tested one. Recommendation: the first doctor build records the actual behaviour and the template is corrected from that fact.
9. **Where TestFlight sits on the ladder.** An upload proves packaging only; a TestFlight install on a real device proves device-only features. Recommendation: uploads are evidence for a release checklist, not a ladder step; a recorded device check of the device-only list is what lets those rows reach `Live Proof`, and `Operational` for the app requires a TestFlight or App Store build in real use.
10. **Testing on the macOS host.** Running platform-neutral package tests with `swift test` on macOS is much faster, but the host differs from iOS. Recommendation: allow it for the inner loop only; gates always run on the simulator.
11. **Parallel iOS makers.** Device clones and separate DerivedData make parallel builds possible, but Xcode builds are CPU-bound and three concurrent builds on one Mac can be slower than serial. Recommendation: at most two concurrent iOS build-and-test agents on this machine; UI lanes serialized per device; measure once and record in `facts.md`.

---

## 9. Skill text candidates

**1. When to load the iOS pack.**
Load `references/ios.md` when the repository contains an `.xcodeproj`, `.xcworkspace`, `project.yml`, `Project.swift`, or a `Package.swift` that declares iOS, or when the goal mentions iPhone, iPad, iOS, SwiftUI or the App Store. iOS builds, tests and screenshots run only on this Mac with Xcode; never assign them to a cloud routine or remote agent.

**2. Preflight before any iOS work.**
Run `scripts/ios/doctor.sh` first. It pins the Xcode path, records Xcode and runtime builds, resolves simulators by role to UDIDs, checks free disk, and tries the Simulator MCP. If the MCP fails, record the exact message, tell the owner the fix once in the run summary, and continue with `simctl` and XCUITest. A check performed by an unavailable tool has not been performed.

**3. Project setup.**
For a new app, describe the project in `project.yml` for XcodeGen and put all modules in one local Swift package under `Packages/`. Do not commit or hand-edit the generated `.xcodeproj`. Write test plans as JSON files and check them in. For an existing app, keep its format; converting the project is a migration and needs its own spec line.

**4. Always use the scripts.**
Build, test, launch and capture through `scripts/ios/*.sh`, which fix the Xcode path, the simulator UDID, the derived-data directory, the package directory and the result-bundle path. Do not type `xcodebuild` or `simctl` commands from memory when a script exists. Address simulators by UDID; never pass `booted`.

**5. Prove tests actually ran.**
Before running a lane, enumerate its tests with `-enumerate-tests` and save the JSON. After running, read the summary with `xcresulttool`. The lane fails if the executed count is zero or lower than the enumerated count, whatever the exit code says.

**6. Prove which build you are looking at.**
Every build sets `DRIVE_BUILD_HASH` to the short git hash, and the app's Info.plist carries it as `DriveBuildHash`. Before collecting any screenshot, tree dump or live evidence, read that key from the installed app with `simctl get_app_container` and `plutil`. If it does not equal HEAD, the evidence is invalid.

**7. Clean in order, and only twice.**
When results contradict the code, clean before debugging: remove built products, then the whole derived-data directory, then the package checkouts, then uninstall the app, then erase the simulator. Record which step fixed it. If the same symptom needs the same clean a second time, stop cleaning and find the cause.

**8. Signing and accounts.**
Build for the simulator without a development team. If the spec needs Sign in with Apple, push, passkeys, App Groups or iCloud, ask the owner once for the Team ID and bundle identifier, build those features behind protocols meanwhile, and mark them Partial with the reason "blocked on team". Never sign in to an Apple account, never enter keys or passwords, and do not disable code signing to speed up builds.

**9. Concurrency.**
Use Swift 6 language mode with strict concurrency complete and main-actor default isolation. Move heavy work off the main actor explicitly. Do not add `@unchecked Sendable`, `nonisolated(unsafe)`, `MainActor.assumeIsolated`, `@preconcurrency` on first-party imports, or `Task.detached` unless a comment names the invariant that makes it safe and a test exercises it. Route concurrency errors you cannot fix in one attempt to an `opus` agent.

**10. Architecture defaults.**
SwiftUI with `@Observable` models; one package with Core, Networking, Persistence, Sync, DesignSystem, one product per feature, and a thin app target that wires dependencies. Generate the API client from the backend's OpenAPI document and commit the output with a drift test. Keep the local database as the UI's source of truth, queue writes in an outbox with idempotency keys, and never make correctness depend on a background task running.

**11. Tests that hold up under parallelism.**
Make every user intent an async method that returns when state has settled, and assert after awaiting it. Stub the network per test with a unique base-URL host so parallel tests cannot share responses. Inject clocks. Never wait with `Task.sleep`. Use real SQLite or SwiftData stores in memory rather than fakes, and load stub responses from fixtures that the backend's contract tests also validate.

**12. Permissions.**
Pre-grant permissions with `simctl privacy` for deterministic flows, and keep one UI test per protected resource that resets the permission and accepts the real system prompt. That test is the only thing that catches a missing usage-description key before a device does.

**13. Simulator MCP use.**
Use the MCP to explore, to walk flows as a reviewer, and to read the accessibility tree. Assert text and structure from `inspect`, not from pixels, and pair it with a screenshot when something could be covered. Encode any flow that must be repeated, including every Live Proof flow, as an XCUITest in a test plan.

**14. Device-only features.**
Camera capture, background task scheduling, passkeys and real push delivery cannot be fully exercised in the simulator. List them in STATUS.md from the first day, keep them at Partial until a check on a physical device is recorded, and test their logic directly with unit tests in the meantime.

**15. Design tokens in code.**
Generate colours, spacing, radii and font roles into `DesignSystem` from `design/tokens.json`, with light, dark and increased-contrast variants, and commit the output with a drift test. Fail the fast lane on colour literals, fixed font sizes and hex strings outside `DesignSystem`. Use text styles so Dynamic Type works, and check primary screens at the largest accessibility size.

**16. Local Proof and Live Proof for iOS.**
Local Proof: the project regenerates, builds for the simulator with first-party warnings as errors, and the fast, UI and snapshot lanes pass with executed counts matching enumeration, accessibility audits clean, drift checks green, and the verifier's mutations caught. Live Proof: the HEAD build, confirmed by its build hash, runs on a recorded simulator against the deployed backend; the Live plan passes; primary screens show server values in the accessibility tree that match a backend read; the UI reviewer passed the captured matrix; and device-only features are listed as unproven.

**17. Release is a later phase.**
From the first commit keep a privacy manifest, a data inventory for App Privacy answers, usage strings and an export-compliance decision current. At release, give the owner one complete list of account actions he must take, then archive and export with the App Store Connect key he placed on disk. An upload proves packaging only. Publishing to the App Store is always his explicit decision.

**18. `references/ios.md` skeleton.**
The reference file carries, in this order: the loading conditions (passage 1); the doctor procedure and `devices.json` roles (section 4.2); the project template, xcconfig and signing notes (4.3); the fixed-path variables, build-once-test-many commands, enumeration guard, run and simctl command block, MCP rules and clean ladder (4.4); the per-host network stub, the async-intent testing rule and the minimal suite table (4.5); the architecture defaults as a numbered list with "verify at project time" items (4.6); the iOS design-contract additions and token lint (4.7); the release checklist and commands (4.8); the Local Proof and Live Proof gates (4.9); the conditionals list (section 5); and the failure-mode table (section 7) condensed to symptom, cause and first action. Keep it under 700 lines by linking to reports 08 and 09 for test-lane commands, snapshot settings and the capture matrix rather than copying them.
