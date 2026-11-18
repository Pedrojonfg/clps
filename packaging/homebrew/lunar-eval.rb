# Homebrew cask. Lives in a tap repo named `homebrew-clps` (github.com/Pedrojonfg/homebrew-clps)
# at Casks/lunar-eval.rb, so users run: brew install --cask Pedrojonfg/clps/lunar-eval
# Update version and sha256 for every release (see packaging/README.md).
cask "lunar-eval" do
  version "X.Y.Z"
  sha256 "0000000000000000000000000000000000000000000000000000000000000000"

  url "https://github.com/Pedrojonfg/clps/releases/download/v#{version}/lunar-eval_#{version}_aarch64.dmg"
  name "lunar-eval"
  desc "Landing-site and time-window evaluator for the lunar south pole"
  homepage "https://github.com/Pedrojonfg/clps"

  depends_on arch: :arm64   # CI builds Apple Silicon only

  app "lunar-eval.app"

  # The build is unsigned: drop the quarantine flag so Gatekeeper does not report it as damaged.
  postflight do
    system_command "/usr/bin/xattr",
                   args: ["-dr", "com.apple.quarantine", "#{appdir}/lunar-eval.app"],
                   sudo: false
  end

  zap trash: [
    "~/Library/Caches/com.lunareval.desktop",
    "~/Library/Application Support/com.lunareval.desktop",
  ]
end
