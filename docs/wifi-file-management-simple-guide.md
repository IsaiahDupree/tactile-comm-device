# Simple WiFi File Management Guide
## For Healthcare Professionals Using the Tactile Communication Device

### What This Guide Covers
This guide will help you wirelessly manage files on your patient's tactile communication device. You'll learn how to:
- Add new audio files to the device
- Remove old or unwanted files
- Browse what's currently stored on the device
- Do all of this without cables or removing the SD card

---

## Getting Started - What You Need

**Before you begin, you'll need:**
- The tactile communication device (powered on)
- A computer, tablet, or smartphone with WiFi
- Audio files you want to add (MP3 format works best)

**No technical experience required** - this guide uses simple, step-by-step instructions.

---

## Step 1: Connect to the Device

### Option A: Use the Device's Built-in WiFi (Easiest)
The device creates its own WiFi network that you can connect to directly.

1. **On your computer/phone, look for WiFi networks**
2. **Find and connect to:** `TCD-Device`
3. **Enter password:** `tcd12345`
4. **Wait for connection** (you'll see "Connected" or similar)

✅ **You're now connected!** The device is at address: `192.168.4.1`

### Option B: Connect Device to Your Existing WiFi
If you prefer to use your facility's WiFi network, you'll need to configure the device first (see Advanced Setup section).

---

## Step 2: Access the File Manager

### Using a Web Browser (Recommended for Beginners)

1. **Open any web browser** (Chrome, Firefox, Safari, Edge)
2. **Type in the address bar:** `http://192.168.4.1/`
3. **Press Enter**

You should see a simple file browser showing the device's contents.

**If you see folders like:**
- `/AUDIO/` - Contains the sound files
- `/CONFIG/` - Contains device settings
- `/ANNOUNCE/` - Contains system announcements

✅ **Success!** You're now viewing the device's files.

---

## Step 3: Managing Files

### Adding New Audio Files

**To upload a new sound file:**

1. **Navigate to the AUDIO folder** by clicking on it
2. **Click "Choose File"** button at the bottom
3. **Select your MP3 file** from your computer
4. **Click "Upload to current path"**
5. **Wait for upload to complete** (you'll see progress)

**File Naming Tips:**
- Use simple names like: `001.MP3`, `002.MP3`, `HELLO.MP3`
- Avoid spaces or special characters
- Keep names short (8 characters or less before the .MP3)

### Removing Unwanted Files

**To delete a file:**

1. **Find the file** you want to remove
2. **Click "Delete"** next to the file name
3. **Confirm** when asked "Are you sure?"

⚠️ **Warning:** Deleted files cannot be recovered. Make sure you want to remove them.

### Browsing Existing Files

**To see what's on the device:**

1. **Click on folders** to open them (like `/AUDIO/`)
2. **View file names and sizes** in the list
3. **Click "Download"** to save a copy to your computer

---

## Step 4: Organizing Patient Files

### Recommended Folder Structure

For easy management, organize files by patient or category:

```
/AUDIO/
  ├── PATIENT_A/
  │   ├── GREETINGS.MP3
  │   ├── NEEDS.MP3
  │   └── RESPONSES.MP3
  ├── PATIENT_B/
  │   ├── FAMILY.MP3
  │   └── COMFORT.MP3
  └── COMMON/
      ├── YES.MP3
      ├── NO.MP3
      └── HELP.MP3
```

### Creating New Folders

**To make a new folder:**

1. **Navigate to where you want the folder**
2. **Upload a file with the folder name in the path**
   - Example: Upload to `/AUDIO/PATIENT_A/HELLO.MP3`
   - This creates the `PATIENT_A` folder automatically

---

## Troubleshooting Common Issues

### "Cannot Connect to TCD-Device"

**Try these solutions:**
1. **Check device power** - Make sure it's turned on
2. **Move closer** - WiFi range is limited
3. **Restart device** - Power off and on again
4. **Check password** - Use `tcd12345` exactly

### "Page Cannot Be Displayed"

**Try these solutions:**
1. **Check address** - Use `http://192.168.4.1/` exactly
2. **Wait longer** - Device may be starting up
3. **Try different browser** - Chrome usually works well
4. **Disable VPN** - Turn off any VPN software

### "Upload Failed" or "File Not Found"

**Try these solutions:**
1. **Check file size** - Very large files may not work
2. **Use MP3 format** - Other formats may not be supported
3. **Simplify filename** - Use only letters and numbers
4. **Check available space** - Device storage may be full

### "Delete Not Working"

**Try these solutions:**
1. **Refresh the page** - Click browser refresh button
2. **Try exact filename** - Case matters (HELLO.MP3 vs hello.mp3)
3. **Check if file is in use** - Device may be playing the file

---

## Advanced Setup (Optional)

### Connecting to Your Facility WiFi

If you want the device to connect to your existing WiFi network:

1. **Create a configuration file** with these contents:
   ```
   SSID=YourWiFiNetworkName
   PASS=YourWiFiPassword
   TOKEN=SecurePassword123
   ```

2. **Save as:** `WIFI.CFG`

3. **Upload to:** `/CONFIG/WIFI.CFG` on the device

4. **Restart the device** - It will connect to your network

**Benefits:**
- Device gets internet access
- Can be accessed from anywhere on your network
- More secure with password protection

### Using Password Protection

For added security, you can require a password for file changes:

1. **Add to your web browser address:** `?token=SecurePassword123`
   - Full address: `http://192.168.4.1/?token=SecurePassword123`

2. **This prevents unauthorized changes** to device files

---

## Quick Reference

### Essential Addresses
- **Device file manager:** `http://192.168.4.1/`
- **With password:** `http://192.168.4.1/?token=YourPassword`

### WiFi Connection
- **Network name:** `TCD-Device`
- **Password:** `tcd12345`

### File Management
- **Upload:** Choose File → Upload to current path
- **Download:** Click "Download" next to file
- **Delete:** Click "Delete" next to file (be careful!)
- **Browse:** Click folder names to open them

### Best Practices
- ✅ Use simple filenames (001.MP3, HELLO.MP3)
- ✅ Keep files organized in folders
- ✅ Test files after uploading
- ✅ Make backups of important files
- ❌ Don't use spaces or special characters in names
- ❌ Don't delete files unless you're sure
- ❌ Don't upload very large files

---

## Getting Help

**If you encounter problems:**

1. **Try the troubleshooting section** above
2. **Power cycle the device** (turn off and on)
3. **Check your WiFi connection**
4. **Contact your IT support** for network issues

**Remember:** This system is designed to be simple and safe. You cannot damage the device by using the file manager incorrectly.

---

*This guide covers the basic file management features. For advanced technical details, refer to the complete technical documentation.*
