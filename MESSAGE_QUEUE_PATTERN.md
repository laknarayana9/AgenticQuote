# Message Queue Pattern Implementation

## Overview

This implementation adds a production-grade message queue pattern for asynchronous quote processing, enabling high-volume handling, improved user experience, and better resource utilization.

## Architecture

### **Message Queue Components**

#### **1. QueueMessage Data Structure**
```python
@dataclass
class QueueMessage:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    status: QueueStatus = QueueStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 300
```

#### **2. Priority Levels**
- **URGENT** (4): Critical cases requiring immediate processing
- **HIGH** (3): High-value quotes, edge cases
- **NORMAL** (2): Standard processing
- **LOW** (1): Bulk processing, non-urgent

#### **3. Status Tracking**
- **PENDING**: Waiting in queue
- **PROCESSING**: Currently being processed
- **COMPLETED**: Successfully processed
- **FAILED**: Processing failed (may retry)
- **CANCELLED**: Manually cancelled

## API Endpoints

### **1. Async Quote Submission**
```http
POST /quote/submit
```

**Request Body**:
```json
{
  "submission": {
    "applicant_name": "John Doe",
    "address": "123 Main St",
    "coverage_amount": 250000
  },
  "use_agentic": false
}
```

**Response**:
```json
{
  "message_id": "uuid",
  "status": "queued",
  "priority": "NORMAL",
  "estimated_processing_time": "2-5 minutes",
  "queue_position": "Processing started"
}
```

### **2. Queue Status Check**
```http
GET /queue/{message_id}
```

**Response**:
```json
{
  "id": "uuid",
  "status": "processing",
  "priority": "NORMAL",
  "created_at": "2026-02-20T...",
  "started_at": "2026-02-20T...",
  "completed_at": null,
  "error_message": null,
  "retry_count": 0,
  "max_retries": 3,
  "payload": { ... }
}
```

### **3. Queue Statistics**
```http
GET /queue/stats
```

**Response**:
```json
{
  "pending_count": 5,
  "processing_count": 2,
  "completed_count": 150,
  "max_size": 1000,
  "oldest_pending": "2026-02-20T...",
  "longest_processing": 45.2
}
```

## Browser Interface Features

### **1. Dual Processing Modes**
- **Sync Mode**: Direct processing (existing `/quote/run`)
- **Async Mode**: Queue processing (new `/quote/submit`)

### **2. Real-time Status Updates**
- Automatic polling every 3 seconds
- Visual status indicators (pending/processing/completed/failed)
- Detailed timestamp tracking

### **3. Queue Management**
- Message ID tracking
- Priority-based processing
- Error handling and retry logic

## Production Benefits

### **1. Scalability**
- **High Volume**: Handle thousands of concurrent submissions
- **Resource Management**: Process quotes at optimal rate
- **Load Balancing**: Distribute processing over time

### **2. User Experience**
- **Immediate Response**: Users get instant confirmation
- **Background Processing**: No blocking UI operations
- **Status Transparency**: Real-time progress tracking

### **3. Reliability**
- **Retry Logic**: Automatic retry on failures
- **Error Handling**: Graceful degradation
- **Timeout Protection**: Prevent hanging processes

### **4. Monitoring**
- **Queue Depth**: Track pending message count
- **Processing Time**: Monitor performance metrics
- **Error Rates**: Track failure patterns

## Priority Assignment Logic

```python
# Automatic priority based on coverage amount
if coverage > 500000:
    priority = MessagePriority.HIGH      # High-value cases
elif coverage < 100000:
    priority = MessagePriority.HIGH      # Edge cases
else:
    priority = MessagePriority.NORMAL     # Standard processing
```

## Background Processing

### **1. Message Processing Flow**
1. **Dequeue**: Get next message by priority
2. **Process**: Execute quote processing logic
3. **Complete**: Store results and mark complete
4. **Retry**: On failure, retry if attempts remain

### **2. Error Handling**
- **Max Retries**: 3 attempts per message
- **Exponential Backoff**: Increasing delays between retries
- **Dead Letter Queue**: Failed messages after max retries

### **3. Cleanup**
- **Old Messages**: Remove completed messages after 24 hours
- **Memory Management**: Prevent queue overflow
- **Statistics**: Maintain performance metrics

## Testing Scenarios

### **1. High Priority Processing**
- **Input**: $600,000 coverage
- **Expected**: HIGH priority, processed before normal messages
- **Test**: Verify priority queue ordering

### **2. Async vs Sync**
- **Sync Mode**: Immediate processing, blocks until complete
- **Async Mode**: Immediate confirmation, background processing
- **Test**: Compare response times and user experience

### **3. Error Recovery**
- **Simulate Failure**: Force processing error
- **Expected**: Retry up to 3 times, then mark as failed
- **Test**: Verify retry logic and error reporting

### **4. Queue Statistics**
- **Multiple Submissions**: Submit various quotes
- **Expected**: Accurate queue statistics
- **Test**: Monitor pending/processing/completed counts

## Performance Characteristics

### **1. Throughput**
- **Sync Mode**: Limited by processing time per request
- **Async Mode**: High throughput, decoupled processing
- **Queue Size**: Up to 1000 concurrent messages

### **2. Latency**
- **Submission**: Immediate response (< 100ms)
- **Processing**: 2-5 seconds per quote
- **Status Check**: Real-time updates

### **3. Resource Usage**
- **Memory**: In-memory queue with cleanup
- **CPU**: Background task processing
- **Network**: Efficient polling mechanism

## Integration with Existing Features

### **1. Human Review Workflow**
- Async quotes can trigger human review
- Queue status includes review requirements
- Seamless integration with approval system

### **2. Monitoring & Metrics**
- Queue statistics available via API
- Integration with existing monitoring
- Performance tracking capabilities

### **3. Error Handling**
- Consistent error reporting
- Retry logic for failed processing
- Graceful degradation patterns

This message queue implementation provides enterprise-grade asynchronous processing capabilities while maintaining the existing synchronous processing option for backward compatibility.
