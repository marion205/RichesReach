# Development Scripts

## React Native Reset Script

### Quick Reset (No Simulator Erase)
```bash
./rn-reset.sh --skip-erase
```

### Full Reset (Erases All Simulators)
```bash
./rn-reset.sh
```

### Verbose Output
```bash
./rn-reset.sh --verbose
```

### What It Does
1. Kills Simulator.app and Expo processes
2. Clears Watchman file watches
3. Removes Metro/Expo caches
4. Clears Xcode derived data
5. Launches iOS Simulator
6. (Optional) Erases all simulator data
7. Lists available simulators

### When to Use
- Metro cache corruption
- Watchman file-watching loops
- Expo CLI crashes
- Simulator state bloat
- After dependency upgrades
- Before performance benchmarks

### Time
~10-30 seconds (simulator erase takes longest)

### Requirements
- Xcode CLI tools (`xcode-select --install`)
- Watchman (`brew install watchman`)

---

## Android Reset (Cross-Platform)

```bash
# Kill ADB server
adb kill-server && adb start-server

# Clean Gradle cache
cd android && ./gradlew clean && cd ..

# Clear Gradle caches
rm -rf ~/.gradle/caches/
```

---

## VS Code Integration

Add to `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Reset RN Environment",
      "type": "shell",
      "command": "./rn-reset.sh",
      "problemMatcher": []
    }
  ]
}
```

---

## Shell Alias

Add to `~/.zshrc` or `~/.bashrc`:

```bash
alias rnreset='cd /Users/marioncollins/RichesReach && ./rn-reset.sh'
```

Then use: `rnreset` from anywhere.

