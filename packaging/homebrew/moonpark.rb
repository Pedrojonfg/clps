# Homebrew cask. Lives in a tap repo named `homebrew-moonpark` (github.com/Pedrojonfg/homebrew-moonpark)
# at Casks/moonpark.rb, so users run: brew install --cask Pedrojonfg/moonpark/moonpark
# Update version and sha256 for every release (see packaging/README.md).
cask "moonpark" do
  version "X.Y.Z"
  sha256 "0000000000000000000000000000000000000000000000000000000000000000"

  url "https://github.com/Pedrojonfg/moonpark/releases/download/v#{version}/moonpark_#{version}_aarch64.dmg"
  name "moonpark"
  desc "Landing-site and time-window evaluator for the lunar south pole"
  homepage "https://github.com/Pedrojonfg/moonpark"

  depends_on arch: :arm64   # CI builds Apple Silicon only

  app "moonpark.app"

  # The build is unsigned: drop the quarantine flag so Gatekeeper does not report it as damaged.
  postflight do
    system_command "/usr/bin/xattr",
                   args: ["-dr", "com.apple.quarantine", "#{appdir}/moonpark.app"],
                   sudo: false
  end

  zap trash: [
    "~/Library/Caches/com.moonpark.desktop",
    "~/Library/Application Support/com.moonpark.desktop",
  ]
end
