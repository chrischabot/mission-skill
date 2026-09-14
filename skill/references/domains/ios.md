# iOS domain reference

Read this file when the iOS pack activates (section 1): at intake, before design, before any Swift
or project file is written, and again before verification, capture and live proof. It decides how
the toolchain is pinned, how a new app is laid out and an existing one left alone, which repo
scripts every agent uses, how tests prove they ran, how the app is driven with and without the
Simulator MCP, the architecture and design defaults, the capture matrix, which features stay
unproven in the simulator, and what Local Proof, Live Proof and Operational mean for a native iOS
app. Examples use an app called Sample with bundle id `com.example.sample`.

**Contents.** 1 Activation · 2 The one rule · 3 Toolchain preflight · 4 Project setup · 5 Repo
scripts and the loop · 6 Driving the app · 7 Testing · 8 Architecture defaults · 9 Design contract
and tokens · 10 State harness and capture matrix · 11 Device-only and team-blocked features · 12 SDK
and platform requirements · 13 Release path · 14 What the rungs mean · 15 Failure modes · Learned constraints

## 1. Activation

The pack is active when the repository contains a `*.xcodeproj`, `*.xcworkspace`, `project.yml`,
`Project.swift`, or a `Package.swift` whose platforms include `.iOS`, or when the goal, SPEC.md or
DESIGN.md names iPhone, iPad, iOS, SwiftUI, UIKit or the App Store. It confirms `native-platform`
and `ui`. The orchestrator then quotes the applicable Learned constraints, at most ten,
under "Lessons that apply to this task" in every brief for `drive:architect`, `drive:designer`,
`drive:implementer`, `drive:severe-tester`, `drive:verifier` and `drive:ui-reviewer`; writes
GOAL.md's `live means:` as "the HEAD build on a named simulator against <deployed backend URL>" or
"not applicable: no backend"; runs section 3 before planning; and adds the rows in sections 11 and 14.

In an existing app, archaeology records in `.drive/how-it-works.md`: project format and generator,
schemes and test plans (`xcodebuild -list -json`), deployment target, Swift mode and concurrency
settings, state style (Observation, `ObservableObject`, TCA, UIKit), persistence, dependency
manager, documented Xcode version, and today's test command with its pass count as the baseline.
iOS work runs only on a Mac with Xcode; a cloud routine or remote agent would report success on
work that never touched a simulator.

## 2. The one rule

Nothing about an iOS app is proven unless it ran on a simulator named by UDID, from a build stamped
with HEAD, against a named data source (fixtures or a backend URL), with all three in the evidence.
Build, test, install, launch and capture only through section 5's scripts, never from memory.

## 3. Toolchain preflight

Run the project's `scripts/ios/doctor.sh` (before it exists, these commands inline) at intake, after
any Xcode or runtime change, and whenever a build fails in a way that does not point at source.

```bash
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer   # pin; never rely on xcode-select
xcodebuild -version; swift --version; ls -d /Applications/Xcode*.app
xcrun simctl list runtimes -j; xcrun simctl list devicetypes -j; xcrun simctl list devices available -j
xcodegen --version; df -h "$HOME"                                  # tuist version if Project.swift; fail under 20 GB free
```

1. Pin the developer directory in every script (an existing project's documented Xcode wins).
2. Create dedicated devices (`xcrun simctl create drive-sample-phone <device type id> <runtime id>`)
   and record them by role in `.drive/local/ios/devices.json` (machine-local) as `{ "phone": {name,
   udid, runtime_build}, ... }`: `phone` iPhone 17 Pro; `small` iPhone 17e, or iPhone SE (3rd
   generation) for the smallest screen; `large` iPhone 17 Pro Max (6.9-inch store screenshots);
   `tablet` iPad Pro 13-inch (M5) for iPad apps. Runtime builds can share an identifier; record both.
3. If the deployment target exceeds the newest runtime, run `xcodebuild -downloadPlatform iOS` and
   record it in DECISIONS.md with undo `xcrun simctl runtime delete <identifier>`; under 40 GB free
   or if it asks for an account, test on the newest runtime and record the minimum as untested.
4. Boot and wait with `xcrun simctl bootstatus <udid> -b`. In the Desktop app, probe the Simulator
   MCP with one `control screenshot` on the phone UDID. If it reports "Xcode is installed but not
   selected", that is an owner action, stated once in STATE.md and the final report: run
   `sudo xcode-select -s /Applications/Xcode.app/Contents/Developer` in a terminal. Never run sudo
   yourself. Continue on the simctl and XCUITest route.
5. Write dated results to STATE.md "Verified facts": every installed Xcode with its path and build
   and which one `DEVELOPER_DIR` selects, Swift, runtime builds (two can share one identifier; record
   both), whether a runtime for the deployment target exists, role UDIDs, generator version, MCP
   status or its exact error, free disk. These facts differ per machine; never copy them from another run.

## 4. Project setup

| Situation | Use |
|---|---|
| New app | XcodeGen `project.yml` plus one local Swift package under `Packages/` for every module; `Sample.xcodeproj` generated and gitignored |
| New app past roughly ten targets or extensions | Tuist, with the reason in DECISIONS.md |
| Existing `.xcodeproj` or `.xcworkspace` | keep its format exactly; add files through buildable folders or existing groups |
| Existing XcodeGen or Tuist project | run its generator; never hand-edit the generated project |
| An app that is only a Swift package | refuse: the iOS app product works only in Swift Playgrounds packages |

Converting an existing project's format is a `move` sub-goal, never a setup step; new apps generate
from text because agents edit YAML reliably and corrupt `project.pbxproj` easily. Layout:
`project.yml`, `Configs/`, `App/` (entry, wiring, Info.plist, assets, `PrivacyInfo.xcprivacy`),
`AppUITests/`, `TestPlans/{Fast,UI,Live}.xctestplan`, `Packages/` (`Sources/<Module>`, `Tests/`),
`scripts/ios/`, `openapi/`. `.gitignore` gains `Sample.xcodeproj/`, `.build/` and `.drive/local/`.

```yaml
name: Sample
options: { bundleIdPrefix: com.example, deploymentTarget: { iOS: "26.0" }, projectFormat: xcode16_0, createIntermediateGroups: true }
configFiles: { Debug: Configs/Debug.xcconfig, Release: Configs/Release.xcconfig }
packages: { SamplePackages: { path: Packages } }
targets:
  Sample:
    type: application
    platform: iOS
    sources: [{ path: App, type: syncedFolder }]
    dependencies: [{ package: SamplePackages, product: AppFeature }]
    info:
      path: App/Info.plist
      properties: { UILaunchScreen: {}, DriveBuildHash: $(DRIVE_BUILD_HASH), API_BASE_URL: $(API_BASE_URL) }
    settings: { base: { PRODUCT_BUNDLE_IDENTIFIER: com.example.sample, ASSETCATALOG_COMPILER_APPICON_NAME: AppIcon } }
  SampleUITests: { type: bundle.ui-testing, platform: iOS, sources: [AppUITests], dependencies: [{ target: Sample }] }
schemes:
  Sample:
    build: { targets: { Sample: all, SampleUITests: [test] } }
    test: { config: Debug, testPlans: [{ path: TestPlans/Fast.xctestplan, defaultPlan: true }, { path: TestPlans/UI.xctestplan }, { path: TestPlans/Live.xctestplan }] }
    archive: { config: Release }
```

```
// Configs/Base.xcconfig, included by Debug.xcconfig and Release.xcconfig
SWIFT_VERSION = 6.0
SWIFT_STRICT_CONCURRENCY = complete
SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor
SWIFT_APPROACHABLE_CONCURRENCY = YES
SWIFT_TREAT_WARNINGS_AS_ERRORS = YES
CURRENT_PROJECT_VERSION = 1
DRIVE_BUILD_HASH = unknown
API_BASE_URL = http:/$()/localhost:8787
DEVELOPMENT_TEAM =
CODE_SIGN_IDENTITY[sdk=iphonesimulator*] = -
```

| Rule | Detail |
|---|---|
| Build stamp | the short hash goes in the custom Info.plist key `DriveBuildHash` from `DRIVE_BUILD_HASH`, never in `CFBundleVersion`, which App Store Connect requires to be period-separated integers |
| Test plans | hand-written JSON (`configurations`, `defaultOptions`, `testTargets`), since XcodeGen does not generate them; after writing one run `xcodebuild -showTestPlans -scheme Sample` and the section 5 enumeration |
| Configurations | Debug and Release only; environments are build settings plus launch arguments (`-API_BASE_URL` lands in `UserDefaults`, read before the Info.plist value) |
| Signing | simulator builds use no team; record the first build's outcome and `codesign -d --entitlements - <app>` in STATE.md; never `CODE_SIGNING_ALLOWED=NO`, which drops entitlements and breaks Keychain groups |
| Package pins | commit `Configs/Package.resolved`; `gen.sh` copies it to `Sample.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved`; a deliberate dependency change runs `xcodebuild -resolvePackageDependencies` and copies it back; confirm the path on first generation |
| Unit tests | live in the package and run on the simulator; add an app-hosted `AppTests` target only when a test needs the assembled app |

## 5. Repo scripts and the loop

Every script sources `scripts/ios/env.sh`, which fails fast if a value is missing:

```bash
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
SLOT=${DRIVE_IOS_SLOT:-main}; DD=.build/ios/DerivedData-$SLOT; SPM=.build/ios/SourcePackages
SHA=$(git rev-parse --short HEAD); RES=.drive/local/ios/results/$SHA; mkdir -p "$RES"
UDID=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]]["udid"])' .drive/local/ios/devices.json "${DRIVE_IOS_ROLE:-phone}")
BUNDLE=com.example.sample; OUT=${DRIVE_PROOF_DIR:-$RES}   # the proof round directory when a verifier runs it
```

| Script | Does | Fails when |
|---|---|---|
| `doctor.sh` | section 3 | any preflight item is untrustworthy |
| `gen.sh` | `xcodegen generate --spec project.yml`, copies `Package.resolved`, `xcodebuild -list -json -project Sample.xcodeproj` | expected schemes or targets are absent |
| `build.sh` | `gen.sh`, then `build-for-testing` once per commit | build fails; prints only extracted errors |
| `test.sh <fast\|ui\|snap\|live>` | enumerate, `test-without-building`, summarize | enumeration empty, executed below enumerated, any failure, a skip without a quarantine entry |
| `install.sh`, `launch.sh <state> [args]` | boot, install, read the stamp back; launch with the state harness | stamp differs from HEAD |
| `capture.sh <screen>...` | section 10 matrix into `$OUT/shots/` with `manifest.json` | stamp mismatch or an incomplete manifest row |
| `live.sh` | Live plan against `$API_BASE_URL` plus backend read-back | any section 14 Live Proof item missing |
| `tokens.sh [--check]`, `clean.sh <step>` | section 9 generation; one step of the clean ladder | `--check` finds output differing from committed |

Build once and test many, so every lane tests the same binary:

```bash
xcodebuild build-for-testing -project Sample.xcodeproj -scheme Sample -configuration Debug \
  -destination "id=$UDID" -destination-timeout 120 -derivedDataPath "$DD" \
  -clonedSourcePackagesDirPath "$SPM" -onlyUsePackageVersionsFromResolvedFile \
  -skipPackagePluginValidation -skipMacroValidation \
  -resultBundlePath "$RES/build.xcresult" DRIVE_BUILD_HASH="$SHA" > "$RES/build.log" 2>&1 \
  || xcrun xcresulttool get build-results --path "$RES/build.xcresult" --compact
```

The skip flags trust every macro and plugin, so they live only in scripts with a committed
`Package.resolved`; a new macro- or plugin-bearing package is a DECISIONS.md entry whose resolved
diff the verifier reads. Agents get the extracted file, line and message, never the build log.

Prove tests ran by enumerating before a lane and comparing after it:

```bash
xcodebuild test-without-building -project Sample.xcodeproj -scheme Sample -testPlan Fast -destination "id=$UDID" \
  -derivedDataPath "$DD" -enumerate-tests -test-enumeration-style flat -test-enumeration-format json \
  -test-enumeration-output-path "$OUT/enumerate-fast.json"
xcodebuild test-without-building -project Sample.xcodeproj -scheme Sample -testPlan Fast -destination "id=$UDID" \
  -derivedDataPath "$DD" -resultBundlePath "$RES/fast.xcresult"
xcrun xcresulttool get test-results summary --path "$RES/fast.xcresult" > "$OUT/summary-fast.json"
```

The lane fails when enumeration is empty, the executed count is below it, or a named test is
absent, whatever the exit code; learn the summary keys once with `--schema` and record them. UI and
Live lanes add `-parallel-testing-enabled NO -collect-test-diagnostics on-failure`. For a filtered
run, enumerate `-only-testing:SampleTests/Suite/name()` with one and two pairs of parentheses and
record the form that selects the test.

Prove the installed build is HEAD before collecting any evidence:

```bash
xcrun simctl bootstatus "$UDID" -b && xcrun simctl install "$UDID" "$DD/Build/Products/Debug-iphonesimulator/Sample.app"
APP=$(xcrun simctl get_app_container "$UDID" "$BUNDLE" app)
test "$(plutil -extract DriveBuildHash raw "$APP/Info.plist")" = "$SHA" || { echo "wrong build"; exit 1; }
```

Clean only when results contradict the code (old behaviour after an edit, `No such module` for an
existing module, a crash in deleted code), one step at a time: remove `$DD/Build/Products`; remove
`$DD`; remove `$SPM` and re-resolve; uninstall the app; shut down and `simctl erase` the device. Log
each step in the workaround ledger; the same clean needed twice opens an investigation.

In the shared checkout each concurrent iOS agent gets its own `DRIVE_IOS_SLOT` and a cloned device
(`xcrun simctl clone <udid> drive-sample-phone-<slot>`). Run at most two iOS build-and-test agents
at once and one UI lane per device; the integrator runs the full gate serially on slot `main`.

## 6. Driving the app

The Simulator MCP (`mcp__Claude_Code_iOS_Simulator__build`, `__control`) exists only in the Desktop
app; headless runs always use simctl plus XCUITest. Verdicts and manifests name the surface
(`ios-simulator-mcp` or `xcuitest+simctl`); a check whose tool was unavailable has not been performed.

| MCP rule | Why |
|---|---|
| Probe with `control screenshot` on the UDID; on error record the message and fall back; pass `device` as a UDID, never a name | names repeat across runtimes |
| Use MCP `build` (absolute `project_path`, after `gen.sh`) for exploration only; gates use `build.sh` | it trusts macros implicitly and writes no result bundle |
| After `control launch`, run the section 5 stamp read-back | the previous install survives a failed build |
| Assert text and structure from `control inspect` (labels, values, frames in points); pair with a screenshot where something could be covered; tap frame centres; start swipes more than 4 points from an edge | `inspect` omits hidden and off-screen elements and cannot see occlusion; edge swipes become OS gestures |
| Encode any flow that must repeat, including every Live Proof flow, as XCUITest | MCP walkthroughs are for discovery and the reviewer's own look |

The simctl and XCUITest route, always available:

```bash
SIMCTL_CHILD_DRIVE_LOG=1 xcrun simctl launch --terminate-running-process --stdout="$RES/app.out" \
  --stderr="$RES/app.err" "$UDID" "$BUNDLE" -DriveState loaded -API_BASE_URL "$BASE_URL"
xcrun simctl io "$UDID" screenshot --type=png "$OUT/shots/<file>.png"
xcrun simctl openurl "$UDID" "sample://item/123"
xcrun simctl push "$UDID" "$BUNDLE" fixtures/push/new-item.apns   # object with "aps", at most 4096 bytes
xcrun simctl addmedia "$UDID" fixtures/photos/*.heic; xcrun simctl location "$UDID" set 37.3349,-122.0090
xcrun simctl privacy "$UDID" reset all "$BUNDLE"; xcrun simctl keychain "$UDID" reset   # privacy has no camera service
xcrun simctl spawn "$UDID" log stream --style compact --predicate 'subsystem == "com.example.sample"' > "$RES/os.log" &
```

Never pass `booted`; with two booted simulators it picks one silently. Here the tree comes from
XCUITest: queries assert label, value and frame, and capture tests attach `app.debugDescription`.

## 7. Testing

Use Swift Testing (parallel by default) for logic, networking, persistence and view models; XCTest
only for XCUITest, performance and the audit. Test plans enable Swift Testing and XCTest
interoperability and set UI crash severity to failure or stricter. `swift test --package-path
Packages` on macOS is for the inner loop only; gates run on the simulator.

| Lane | Plan | Runs | Parallel | Budget |
|---|---|---|---|---|
| fast | Fast | package tests with real in-memory stores and stubbed network; drift, literal and privacy checks | yes | under 90 s warm |
| ui | UI | XCUITest flows on fixtures, audits, launch test, capture tests | no | under 10 min |
| snap | inside Fast or UI | swift-snapshot-testing on signature screens | no | under 2 min |
| live | Live | two or three flows against the deployed backend with a run-scoped test account | no | under 5 min |

**Network stubs.** Parallel tests share responses unless each owns a unique host: `StubURLProtocol`
keeps handlers in a `Mutex<[String: Handler]>` (iOS 18+) keyed by `<uuid>.stub.invalid`, and
`make(handler)` returns an ephemeral `URLSession` with `protocolClasses = [StubURLProtocol.self]` plus
that base URL. Responses load from `Packages/Tests/Fixtures/api/`, which the backend's contract tests
validate. Ledger rows: bodies arrive as `httpBodyStream`; the stub never produces slow, partial or
TLS failures, so timeout and retry claims need a handler throwing `URLError(.timedOut)` or a live check.

**Observation state.** Each intent is an `async` model method that returns once state settles;
tests await it and assert. Use `Observations` only for outside changes, iterating to a predicate
under a task-group timeout (the first element is the current value). Never `Task.sleep`; inject
`any Clock<Duration>` into debounce, retry and expiry; mark main-actor model suites `@MainActor`.

**XCUITest flows.** Every touched element has an `accessibilityIdentifier` from an `AccessibilityIDs`
enum shared by app and tests; visible text is queried only to assert copy; waits use
`waitForExistence(timeout:)`. Each flow ends with the audit and a kept screenshot:

```swift
try app.performAccessibilityAudit(for: [.contrast, .dynamicType, .hitRegion, .sufficientElementDescription, .textClipped]) { issue in
  false  // ignoring needs a comment naming its STATE.md quarantine entry; the verifier greps for it
}
let shot = XCTAttachment(screenshot: XCUIScreen.main.screenshot()); shot.lifetime = .keepAlways; add(shot)
```

Add a `runsForEachTargetApplicationUIConfiguration` launch test, an `XCUIVoiceOverService` primary
flow test, and per protected resource a real-prompt test, since pre-grants hide missing usage keys.

**Snapshots across device, Dynamic Type and dark mode.** Three to five signature screens, with
`.image(layout: .device(config:), precision: 0.99, perceptualPrecision: 0.98, traits:)` in light and
dark at default and `.accessibilityExtraExtraExtraLarge`, recorded and compared on one simulator
model and runtime; after a runtime change re-record with `record: .all` in one commit naming it. UI
tests reach the largest size with `-UIPreferredContentSizeCategoryName
UICTContentSizeCategoryAccessibilityXXXL`; the first such test asserts a label's frame grew.

A minimal hard suite for a mid-sized app (about 15 screens, 30 endpoints, persistence, sync, auth):

| Layer | Count | Tries to break |
|---|---|---|
| Core logic, parameterized | 25 to 40 | boundaries: empty, one, maximum, invalid, time zones, locales |
| Networking | one per endpoint family plus 6 | every fixture decodes; unknown enum values tolerated; 401 refreshes once then signs out; 429 and 5xx back off; offline is a typed error; encoding matches the contract |
| Persistence | 8 to 12 | migration from every shipped schema via stored database files; uniqueness, cascades; large batches; concurrent background writes; corrupt store recovery |
| Sync | 8 to 10 | idempotent outbox replay; conflict policy; mid-batch failure; cursor survives relaunch; deletions both ways |
| View models | 1 to 3 per screen | loading, loaded, empty, error, offline reachable and correct |
| XCUITest flows | 5 to 8 | sign-in, the two primary jobs, a prompt per resource, deep link entry, sign-out clears data; each ends with an audit |
| Snapshots; launch and VoiceOver | 3 to 5 screens; 2 | light and dark at default and AX5; every configuration launches; primary flow works under VoiceOver |
| Live | 2 to 3 | test-account sign-in; a server value on screen; a write read back from the backend |

## 8. Architecture defaults

Unless the project decided otherwise, `drive:architect` applies these and logs results in DESIGN.md.

| Need | Default | Verify at project time |
|---|---|---|
| Target | newest installed SDK; iOS 26.0 for a new consumer app | audience evidence; a runtime at the minimum version is installed |
| UI and state | SwiftUI lifecycle; `@Observable` models owned via `@State`; no `ObservableObject` or Combine in new code; `NavigationStack` with a typed route enum and a tested deep-link parser | no `@State` both defaulted and assigned in `init` (iOS 27 macro) |
| Concurrency | Swift 6 mode, strict complete, main-actor default, approachable concurrency; heavy work leaves the main actor explicitly via `@concurrent` or an actor | each `@unchecked Sendable`, `nonisolated(unsafe)`, `MainActor.assumeIsolated`, first-party `@preconcurrency` or `Task.detached` has an invariant comment and a test; packages dense in isolation work are marked hard so their implementer runs on `opus` |
| Modules | one local package: `Core` (no UI), `Networking`, `Persistence`, `Sync`, `DesignSystem`, one product per feature, `AppFeature`; features never depend on each other; the app target only wires | package test target isolation after the first compile |
| Injection | an `AppDependencies` struct through the environment with `@Entry`; protocols or closure structs; no DI framework | no class instances as `@Entry` defaults |
| Networking | swift-openapi-generator with `swift-openapi-urlsession`, CLI output committed under `Networking/Generated/`, a regenerate-and-diff test, a hand-written facade; hand-written `Codable` only under about ten endpoints with no contract | OpenAPI version (3.1 supported, 3.2 preliminary) and `oneOf` usage |
| Auth | backend sessions in the Keychain; Sign in with Apple when any third-party login exists; passkeys where the backend has WebAuthn; in-app account deletion; a staging-only test-account endpoint for the Live plan | current App Review wording at release |
| Photos and Vision | `PhotosPicker` (no permission to pick); Vision off the main actor on downscaled input | each Vision request in the simulator in week one, with a fallback for failures |
| Persistence | GRDB 7 (SQLiteData for CloudKit) for sync-heavy apps with a backend; SwiftData for simple local models; real store in memory in tests; only `Persistence` imports either | the choice and its reasons |
| Offline and sync | local database is the UI's truth; outbox with client idempotency keys replayed on foreground, reconnect, push and refresh; server cursor | nothing correct depends on a background task running |
| Push, config, logs | backend holds the APNs token key; no secrets in the bundle; `os.Logger` per module with the bundle id as subsystem; MetricKit in production; String Catalogs from the first commit | the owner-set backend secret names |

## 9. Design contract and tokens

`drive:designer` writes `design/DESIGN.md`, `design/tokens.json` and `design/screens.yaml` with the
HIG as the floor and departures logged (an existing app's contract is extracted from what ships).
It also decides the navigation
model (tabs, stack depth, sheets and detents, search, iPad sidebar and window resizing), the Liquid
Glass stance (system materials on bars and controls, custom glass only in named places, contrast
checked under glass), SF Symbols rules, every screen's loading, empty, error, offline, partial and
permission-denied states, a priming screen before each system prompt matching its usage string,
motion and haptics with the Reduce Motion substitute, the Icon Composer `.icon`, and the launch screen.

HIG numbers the contract and the reviewer hold to, verified 2026-09-14:

| Topic | Requirement |
|---|---|
| Targets | controls default to 44×44 pt, 28×28 pt minimum; about 12 pt padding around bezelled elements, 24 pt around unbezelled |
| Text | text styles only (Large Title 34, Title 1 28, Title 2 22, Title 3 20, Headline 17 semibold, Body 17, Callout 16, Subhead 15, Footnote 13, Caption 1 12, Caption 2 11); minimum 11 pt; custom fonts use `relativeTo:` |
| Dynamic Type | usable through AX5 and at least 200 percent enlargement; adjacent views stack and rows grow so text is never cropped |
| Contrast | 4.5:1 up to 17 pt, 3:1 at 18 pt or bold; strive for 7:1 for custom colours in small text |
| Appearance and motion | light and dark both designed and checked with Increase Contrast and Reduce Transparency, separately and together; under Reduce Motion no zooming, scaling or peripheral motion, and axis transitions become fades |
| Layout and RTL | frames inside the safe area, largest and smallest layouts checked first; in right to left flip navigation, progress and directional icons, never logos, checkmarks, clocks, photos or digits |

`scripts/ios/tokens.sh` turns `design/tokens.json` into committed code in
`Packages/Sources/DesignSystem/Generated/`: `.colorset`s with any, dark and high-contrast
appearances, `Color` statics, a `Spacing` enum, radii, and `Font` helpers using text styles or
`relativeTo:`. The fast lane runs `tokens.sh --check` and fails on `Color(red:`, `#colorLiteral`,
`UIColor(red:`, `.font(.system(size:`, hex strings, and padding literals above 4 outside `DesignSystem`.

## 10. State harness and capture matrix

The maker implements Debug-only launch arguments read through `UserDefaults`: `-DriveState
<default|empty|loading|error|offline|long-text|...>` selects fixtures, `-DriveNetwork
<online|offline|slow|fail>` a stub mode, `-DriveScreen <id>` opens a screen, `-API_BASE_URL` the
backend. Long-text fixtures run two to three times normal length, plus a pseudo-localised variant.
`design/screens.yaml` records `build_stamp: { ios: { plist_key: DriveBuildHash } }` and the harness.
`drive:ui-reviewer` runs `capture.sh` itself; screenshots a maker hands over are not evidence.

| Tier | Roles | Appearance | Content size | States |
|---|---|---|---|---|
| primary | `phone` for every declared state; `small` and `large` (or `tablet`) for `default` and the state with the most content | light and dark on `phone`; light elsewhere | `large` for every captured state; `accessibility-extra-extra-extra-large` for `default` and the state with the most content; plus one phone, light, default-state pass with `simctl ui <udid> increase_contrast enabled` | as listed under Roles |
| secondary | phone | light, dark | `large` | default, empty |
| RTL, only if the spec localises | phone | light | `large` | primary flow with `-AppleLanguages '(ar)' -AppleLocale ar_SA` |

The script sets `status_bar "$UDID" override --time 9:41 --batteryState charged --batteryLevel 100
--dataNetwork wifi --wifiBars 3`; per cell checks the stamp, sets `simctl ui` appearance and
`content_size`, launches with `--terminate-running-process` and the harness, waits for the screen's
identifier, and writes `shots/<screen>/<cell>.png`, the cell being
`<role>.<light|dark>.<default|largest|increase-contrast>.<ltr|rtl>.<state>` as `templates/ui-findings.schema.json`
names it (`default` is `large`, `largest` the AX size), with a `.tree.json` and a `sips -Z 2000` `.review.png`; then clears the status bar and restores light and
`large`. Each `manifest.json` row carries UDID, runtime and Xcode builds, appearance, content size,
state, surface, the installed stamp, and data source (`fixture` or backend URL); the reviewer rejects
incomplete rows. Reduce Motion is judged from frames of a `simctl io <udid> recordVideo` recording.

## 11. Device-only and team-blocked features

Give each its own STATUS row at intake, test its logic directly, and record `why:device-only:
<reason>`. Such a row reaches Local Proof without a device; Live Proof needs a `live:` bundle with
`environment: device` from a physical device (the owner's TestFlight install, or a team-signed build
installed with `xcrun devicectl device install app`); it is never Done in a run without the owner's
device, so the run ends `status: stopped` with each such row carrying its `why:` token.

| Feature | Why the simulator falls short | Meanwhile |
|---|---|---|
| Camera capture | no camera; `simctl privacy` has no camera service | picker path in the simulator; capture behind a protocol |
| Background task scheduling | the scheduler cannot be forced by automation | the same sync runs on foreground and is tested directly |
| Real push delivery | `simctl push` bypasses APNs; a real token needs a team | handling tested with payload files |
| Passkeys, Sign in with Apple, App Groups across processes, iCloud | paid team (passkeys also Associated Domains, and unreliable on iOS 26 simulators) | simulator-safe implementation behind a protocol; staging test-account sign-in |
| Neural Engine dependent Vision requests | may differ or fail in the simulator | measured in week one; fallback designed |
| Performance, memory and thermal limits | the host Mac is kinder | a `shim_differences` entry on every iOS bundle |

If the spec needs a team-only capability, do not ask: build behind the protocol, set the rows to
Partial with `why:blocked on team`, and name the Team ID and bundle id as owner steps in the report.
Never sign in to an Apple account, enter credentials, or create App IDs.

## 12. SDK and platform requirements

Verified 2026-09-14 against developer.apple.com. For a decision resting on a row older than 90 days,
re-read the source and record it dated in RESEARCH.md; a change becomes a Learned constraint.

| Requirement | Consequence |
|---|---|
| Apps built with the iOS 27 SDK must adopt the scene-based life cycle or they fail to launch | SwiftUI lifecycle, or `UISceneDelegate` in UIKit apps; an upgrade checks this first |
| Apps must include a launch screen (`UILaunchScreen` or a storyboard key) | `UILaunchScreen: {}` in the template; a check greps Info.plist |
| Xcode 27 (Swift 6.4, iOS 27 SDK) needs macOS Tahoe 26.6 and supports targets iOS 15 to 27; Xcode 26.6 supports 15 to 26.5 | a package declaring iOS 13 fails; bump or replace it, never patch the package cache |
| App Store uploads since 2026-04-28 need Xcode 26 or later and the iOS 26 SDK | release builds use the pinned Xcode |
| Required-reason API declarations enforced since 2024-05-01 | `PrivacyInfo.xcprivacy` from the first commit; `UserDefaults` is a category |
| `@State` is a macro evaluating its initial value once; `PreviewProvider` deprecated; export methods renamed to `app-store-connect`, `release-testing`, `debugging` | no default plus `init` assignment; previews are never evidence; export options use the new names |
| API minimums: `performAccessibilityAudit` iOS 17, `Mutex` iOS 18, `Observations` iOS 26 | a lower target needs replacements |
| `UIDesignRequiresCompatibility` reported ignored with the iOS 27 SDK (secondary sources only) | design for Liquid Glass; check on the first build and record |

## 13. Release path

Release is a later phase entered only when the spec says so. From the first commit agents keep
current: the privacy manifest, with a fast-lane check that required-reason APIs (`UserDefaults`,
file timestamps, `systemUptime`, disk space) have their category; `docs/app-privacy.md`, a data
inventory by type (collected, linked, tracking, purpose, retention, SDK); usage strings;
`ITSAppUsesNonExemptEncryption`; icon, display name, an integer `CURRENT_PROJECT_VERSION`; and store
screenshots on `large` (portrait 1260×2736, 1290×2796 or 1320×2868) and `tablet` (2064×2752 or
2048×2732) at 9:41 with seeded non-personal data and no alpha (`sips -s format jpeg`).

The report gives the owner one complete list: paid team and Team ID, bundle id, App Store Connect
app record, an API key file the owner places where the scripts read it, age rating, pricing, App Privacy
answers, export compliance, TestFlight information. The release script then runs `xcodebuild
archive` (Release, `-destination 'generic/platform=iOS'`, `-allowProvisioningUpdates` with
`-authenticationKeyPath`, `-authenticationKeyID`, `-authenticationKeyIssuerID`, and
`CURRENT_PROJECT_VERSION` and `DRIVE_BUILD_HASH` set) and `xcodebuild -exportArchive` with the same
key flags and an `ExportOptions.plist` of `method` `app-store-connect`, `destination` `upload`;
Transporter is the owner's fallback. An upload proves packaging, not behaviour. Drive never submits
to the App Store; the report says the build is ready and names the owner's step.

## 14. What the rungs mean

| Rung | Means for an iOS app |
|---|---|
| Local Proof | For one commit: preflight recorded; `gen.sh` and `build.sh` green with first-party warnings as errors; fast, UI and snap lanes with executed equal to enumerated and above zero, no failures, no unticketed skips; audits clean; token, OpenAPI and privacy checks green; claim and severe tests pass; the verifier's mutations turned the named tests red; `[ui]` rows carry `shot:` from the reviewer's own fixture capture; a verifier verdict passes. |
| Live Proof | Local Proof set plus a `live:` bundle whose `proof.json` has `environment: live`, `target` the deployed backend URL, `commit`, the commands, and `shim_differences` naming at least the simulator-versus-device differences. Its round holds the backend version; the stamp read from the app on the recorded UDID equal to the commit; the Live plan green with a run-scoped test account; for each primary screen a tree read of a server value beside a `curl` or database read of the same value; the live capture matrix graded pass by `drive:ui-reviewer`; and STATUS naming every device-only and team-blocked row. A simulator against fixtures or a local backend is never Live Proof. |
| Operational | Live Proof set plus an `ops:` file showing: the backend rows Operational; a TestFlight or App Store build mapped to the commit, installed and exercised on a physical device; each device-only row checked there; crash and hang reports received from that build. These need the owner's device and accounts, so before the release phase app rows top out at Live Proof and the report says so in one line. |

Add at intake `the-head-build-on-a-named-simulator-shows-data-from-the-deployed-backend` (live `y`
when there is a backend) and one row per device-only or team-blocked feature.

## 15. Failure modes

| Symptom | Cause | First action |
|---|---|---|
| Green lane on code that no longer exists | stale DerivedData or products | clean ladder step one; per-slot `-derivedDataPath` |
| Lane exits 0 having run nothing | filter parentheses, plan omits a target, scheme lacks the test target | enumeration guard; fix the plan, never the guard |
| Evidence from another OS or device than recorded | `name=` or `OS=` destination, or `booted` | `id=<UDID>` only; runtime build in the manifest |
| Same script, different results | inherited `xcode-select` or PATH chose the other Xcode | `DEVELOPER_DIR` in `env.sh`; Xcode build in every manifest |
| Flaky async test | `Task.sleep`, shared static stub, wrong `Observations` element, animation race | settled intents, per-host stubs, injected clock, `waitForExistence`; after a second flake run `-enableThreadSanitizer YES -test-iterations 50 -run-tests-until-failure` |
| Clean build that races at run time | concurrency escape hatch added to quiet the compiler | verifier greps the hatches; each needs its invariant comment and test |
| Crash at the first permission prompt on a device | missing usage string hidden by a pre-grant | real-prompt UI test per resource |
| Feature called done that cannot work without a team | capability added in the simulator | row at Partial with `why:blocked on team`; Team ID and bundle id named in the report |
| MCP errors read as app crashes | Simulator MCP unavailable or wrong developer directory | record the message, use simctl and XCUITest, name the owner action once |

The lesson loop appends entries below using the lesson template (`templates/lesson.md`), capped at 40 entries.

## Learned constraints
