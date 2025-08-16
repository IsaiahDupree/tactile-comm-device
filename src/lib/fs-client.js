/**
 * Serial File System Protocol Client
 * Implements the M4 FS protocol for atomic SD card updates
 */

const fs = require('fs-extra');
const path = require('path');
const crypto = require('crypto');

class FSClient {
    constructor(ipcRenderer) {
        this.ipc = ipcRenderer;
        this.sessionActive = false;
        this.chunkSize = 512; // Match device buffer size
    }

    /**
     * Calculate CRC32 checksum (matches device implementation)
     */
    calculateCRC32(buffer) {
        // Simple CRC32 implementation - in production, use a proper library
        let crc = 0xFFFFFFFF;
        for (let i = 0; i < buffer.length; i++) {
            crc ^= buffer[i];
            for (let j = 0; j < 8; j++) {
                crc = (crc >>> 1) ^ (crc & 1 ? 0xEDB88320 : 0);
            }
        }
        return (crc ^ 0xFFFFFFFF) >>> 0;
    }

    /**
     * Start a new FS session
     */
    async beginSession() {
        if (this.sessionActive) {
            throw new Error('FS session already active');
        }

        const result = await this.ipc.invoke('send-command', 'FS_BEGIN');
        if (!result.success) {
            throw new Error(`Failed to begin FS session: ${result.message}`);
        }

        this.sessionActive = true;
        return true;
    }

    /**
     * Upload a single file to the device
     */
    async uploadFile(localPath, remotePath, onProgress = null) {
        if (!this.sessionActive) {
            throw new Error('No active FS session');
        }

        try {
            // Read file data
            const fileData = await fs.readFile(localPath);
            const fileSize = fileData.length;
            
            // Calculate CRC32 for entire file
            const fileCRC = this.calculateCRC32(fileData);

            // Send FS_PUT command
            const putCommand = `FS_PUT ${remotePath} ${fileSize} ${fileCRC.toString(16).padStart(8, '0')}`;
            let result = await this.ipc.invoke('send-command', putCommand);
            if (!result.success) {
                throw new Error(`FS_PUT failed: ${result.message}`);
            }

            // Send file data in chunks
            let offset = 0;
            let chunkIndex = 0;
            
            while (offset < fileSize) {
                const chunkEnd = Math.min(offset + this.chunkSize, fileSize);
                const chunk = fileData.slice(offset, chunkEnd);
                const chunkCRC = this.calculateCRC32(chunk);

                // Send FS_DATA command
                const dataCommand = `FS_DATA ${chunkIndex} ${chunk.length} ${chunkCRC.toString(16).padStart(8, '0')}`;
                
                // Send command and binary data
                result = await this.ipc.invoke('send-fs-data', dataCommand, chunk);
                if (!result.success) {
                    throw new Error(`FS_DATA failed at chunk ${chunkIndex}: ${result.message}`);
                }

                offset = chunkEnd;
                chunkIndex++;

                // Report progress
                if (onProgress) {
                    onProgress({
                        file: path.basename(localPath),
                        bytesTransferred: offset,
                        totalBytes: fileSize,
                        progress: (offset / fileSize) * 100
                    });
                }
            }

            // Send FS_DONE command
            result = await this.ipc.invoke('send-command', 'FS_DONE');
            if (!result.success) {
                throw new Error(`FS_DONE failed: ${result.message}`);
            }

            return {
                success: true,
                file: remotePath,
                size: fileSize,
                chunks: chunkIndex,
                crc32: fileCRC
            };

        } catch (error) {
            // Abort the file transfer on error
            await this.ipc.invoke('send-command', 'FS_ABORT');
            throw error;
        }
    }

    /**
     * Upload multiple files in a batch
     */
    async uploadFiles(fileMap, onProgress = null) {
        if (!this.sessionActive) {
            await this.beginSession();
        }

        const results = [];
        const totalFiles = Object.keys(fileMap).length;
        let completedFiles = 0;

        for (const [localPath, remotePath] of Object.entries(fileMap)) {
            try {
                const result = await this.uploadFile(localPath, remotePath, (fileProgress) => {
                    if (onProgress) {
                        onProgress({
                            ...fileProgress,
                            fileIndex: completedFiles,
                            totalFiles: totalFiles,
                            overallProgress: ((completedFiles + fileProgress.progress / 100) / totalFiles) * 100
                        });
                    }
                });

                results.push(result);
                completedFiles++;

                if (onProgress) {
                    onProgress({
                        file: path.basename(localPath),
                        fileIndex: completedFiles,
                        totalFiles: totalFiles,
                        overallProgress: (completedFiles / totalFiles) * 100,
                        completed: true
                    });
                }

            } catch (error) {
                results.push({
                    success: false,
                    file: remotePath,
                    error: error.message
                });
            }
        }

        return results;
    }

    /**
     * Commit all changes atomically
     */
    async commitSession() {
        if (!this.sessionActive) {
            throw new Error('No active FS session');
        }

        try {
            const result = await this.ipc.invoke('send-command', 'FS_COMMIT');
            if (!result.success) {
                throw new Error(`FS_COMMIT failed: ${result.message}`);
            }

            this.sessionActive = false;
            return true;
        } catch (error) {
            // Try to abort on commit failure
            await this.abortSession();
            throw error;
        }
    }

    /**
     * Abort the current session and rollback changes
     */
    async abortSession() {
        if (!this.sessionActive) {
            return true;
        }

        try {
            const result = await this.ipc.invoke('send-command', 'FS_ABORT');
            this.sessionActive = false;
            return result.success;
        } catch (error) {
            this.sessionActive = false;
            throw error;
        }
    }

    /**
     * Sync an entire directory to the device
     */
    async syncDirectory(localDir, remoteDir = '/', onProgress = null) {
        try {
            // Build file map
            const fileMap = await this.buildFileMap(localDir, remoteDir);
            
            // Begin session
            await this.beginSession();

            // Upload all files
            const results = await this.uploadFiles(fileMap, onProgress);

            // Check for errors
            const errors = results.filter(r => !r.success);
            if (errors.length > 0) {
                throw new Error(`Failed to upload ${errors.length} files: ${errors.map(e => e.error).join(', ')}`);
            }

            // Commit changes
            await this.commitSession();

            // Reload device configuration
            await this.ipc.invoke('send-command', 'CFG_RELOAD');

            return {
                success: true,
                filesUploaded: results.length,
                results: results
            };

        } catch (error) {
            // Ensure session is aborted on error
            if (this.sessionActive) {
                await this.abortSession();
            }
            throw error;
        }
    }

    /**
     * Build a map of local files to remote paths
     */
    async buildFileMap(localDir, remoteDir) {
        const fileMap = {};
        
        async function walkDirectory(dir, prefix) {
            const items = await fs.readdir(dir, { withFileTypes: true });
            
            for (const item of items) {
                const localPath = path.join(dir, item.name);
                const remotePath = path.posix.join(prefix, item.name);
                
                if (item.isDirectory()) {
                    await walkDirectory(localPath, remotePath);
                } else {
                    fileMap[localPath] = remotePath;
                }
            }
        }
        
        await walkDirectory(localDir, remoteDir);
        return fileMap;
    }

    /**
     * Get device information
     */
    async getDeviceInfo() {
        const result = await this.ipc.invoke('send-command', 'GET_INFO');
        return result.success;
    }

    /**
     * Reload device configuration without reboot
     */
    async reloadConfig() {
        const result = await this.ipc.invoke('send-command', 'CFG_RELOAD');
        return result.success;
    }
}

module.exports = FSClient;
