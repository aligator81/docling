# Large File Embedding Guide

This guide provides solutions for handling embedding timeouts with large files in the Docling application.

## 🚨 Problem: Embedding Timeout

You're experiencing the error: `⏰ Embedding timed out after 5 minutes`

## ✅ Solutions Implemented

### 1. Enhanced Timeout Configuration

The embedding script has been updated with significantly increased timeouts:

- **Per-chunk timeout**: 30 minutes (increased from 5 minutes)
- **Overall process timeout**: 4 hours (increased from 1 hour)
- **Maximum retries**: 8 attempts per chunk
- **Retry delay**: 15 seconds between retries

### 2. Smart Chunk Splitting

The system now automatically:
- Splits large chunks into smaller sub-chunks
- Uses semantic boundaries (paragraphs, sentences) for better splitting
- Implements emergency mode with even smaller chunks for problematic files

### 3. Emergency Fallback System

When normal processing fails:
1. First attempt with standard chunk sizes
2. Automatic fallback to emergency mode with smaller chunks
3. Comprehensive error handling and logging

## 🛠️ Usage Instructions

### Run with Enhanced Timeouts

```bash
# Standard usage (now with extended timeouts)
python 3-embedding-neon.py --embedding-provider openai

# Resume interrupted processing
python 3-embedding-neon.py --embedding-provider openai --resume
```

### Check Current Configuration

```bash
python embedding_config.py
```

### Analyze and Optimize

```bash
python embedding_optimizer.py
```

## 📊 Configuration Settings

### Current Timeout Settings
- **EMBEDDING_TIMEOUT**: 1800 seconds (30 minutes)
- **PROCESSING_TIMEOUT**: 14400 seconds (4 hours)
- **MAX_RETRIES**: 8 attempts
- **RETRY_DELAY**: 15 seconds

### Chunk Size Settings
- **MAX_CHUNK_SIZE**: 4000 tokens
- **OPTIMAL_CHUNK_SIZE**: 2000 tokens
- **EMERGENCY_CHUNK_SIZE**: 1000 tokens

## 🔧 Advanced Configuration

### Modify Timeout Settings

Edit `embedding_config.py` to adjust settings:

```python
# Increase timeouts for very large files
EMBEDDING_TIMEOUT = 3600  # 1 hour per chunk
PROCESSING_TIMEOUT = 28800  # 8 hours overall
MAX_RETRIES = 12  # More retries for unstable connections
```

### Environment Variables

You can also set these as environment variables:

```bash
export EMBEDDING_TIMEOUT=3600
export PROCESSING_TIMEOUT=28800
export MAX_RETRIES=12
```

## 🎯 Best Practices for Large Files

### 1. Monitor Progress
```bash
# Check the log file for detailed progress
tail -f embedding_process.log
```

### 2. Use Resume Feature
Always use `--resume` flag to continue from interruptions:
```bash
python 3-embedding-neon.py --embedding-provider openai --resume
```

### 3. Check Database Status
```bash
python check_db.py
```

### 4. Optimize Chunk Sizes
If timeouts persist, consider reducing chunk sizes in the chunking step (2-chunking-neon.py).

## 🚀 Performance Tips

### For Very Large Documents (>100MB)
1. **Pre-process documents**: Split into smaller files if possible
2. **Use smaller chunks**: Modify chunking settings in step 2
3. **Monitor memory usage**: Ensure sufficient RAM for processing
4. **Use SSD storage**: Faster I/O for large file operations

### Network Considerations
1. **Stable connection**: Ensure reliable internet for API calls
2. **Rate limiting**: The system includes built-in delays to avoid API limits
3. **Batch processing**: Process documents in smaller batches

## 🔍 Troubleshooting

### Common Issues and Solutions

#### 1. Still Getting Timeouts
- Check internet connection stability
- Verify API key validity and quotas
- Reduce chunk sizes further
- Process documents in smaller batches

#### 2. Memory Issues
- Monitor system memory during processing
- Close other memory-intensive applications
- Consider processing fewer documents simultaneously

#### 3. Database Connection Issues
- Verify Neon database connection string
- Check database performance and limits
- Ensure sufficient database storage

### Diagnostic Commands

```bash
# Check system resources
python check_status.py

# Verify database connectivity
python check_db.py

# Analyze chunk sizes for optimization
python embedding_optimizer.py

# Check embedding progress
python check_chunk_metadata.py
```

## 📈 Monitoring and Logging

### Log Files
- **embedding_process.log**: Detailed processing logs
- **System logs**: Check system resource usage

### Progress Tracking
- Checkpoint files are automatically created
- Resume capability preserves progress
- Detailed progress reporting in logs

## 🆘 Getting Help

If issues persist:

1. **Check logs**: Review `embedding_process.log` for detailed error information
2. **Database status**: Run `python check_db.py` to verify database health
3. **System resources**: Ensure adequate memory and storage
4. **API status**: Check OpenAI/Mistral API status pages

## 📚 Additional Resources

- [OpenAI Embedding API Documentation](https://platform.openai.com/docs/guides/embeddings)
- [Mistral Embedding API Documentation](https://docs.mistral.ai/api/#operation/createEmbedding)
- [Neon Database Documentation](https://neon.tech/docs)

---

**Note**: The enhanced timeout settings should resolve most embedding timeout issues. If problems persist, consider processing documents in smaller batches or contacting support for further optimization.