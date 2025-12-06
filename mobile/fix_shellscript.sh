#!/bin/bash
# Fix shellScript array issue in Xcode project

set -e

cd "$(dirname "$0")"

echo "🔧 Fixing shellScript array issue in Xcode project..."
echo ""

# Clean environment
unset GEM_PATH GEM_HOME RUBY_VERSION RUBY_ROOT MY_RUBY_HOME IRBRC
export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:$PATH"

# Install xcodeproj if needed
if ! gem list xcodeproj -i &>/dev/null; then
  echo "📦 Installing xcodeproj gem..."
  sudo gem install xcodeproj -n /usr/local/bin
fi

# Fix the project
echo "🔨 Fixing project.pbxproj..."
ruby -e "
require 'xcodeproj'
project = Xcodeproj::Project.open('ios/RichesReach.xcodeproj')
fixed = false
project.targets.each do |target|
  target.shell_script_build_phases.each do |phase|
    if phase.shell_script.is_a?(Array)
      phase.shell_script = phase.shell_script.join('\n')
      puts '✅ Fixed shellScript in ' + target.name
      fixed = true
    end
  end
end
project.save
puts 'ℹ️  No fixes needed (shellScript already correct)' unless fixed
"

echo ""
echo "✅ Project fixed!"
echo ""
echo "📦 Now running pod install..."

# Clean and install pods
cd ios
rm -rf Pods Podfile.lock
unset GEM_PATH GEM_HOME
pod install --repo-update

echo ""
echo "✅ Pod install complete!"
echo ""
echo "🚀 You can now run: npx expo run:ios"






