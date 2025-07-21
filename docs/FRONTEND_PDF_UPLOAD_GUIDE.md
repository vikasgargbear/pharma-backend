# Frontend PDF Upload Implementation Guide

## Overview
The backend has PDF upload endpoints ready, but the frontend needs UI components to use them.

## Available Backend Endpoints

### 1. Parse Invoice PDF
```http
POST /api/v1/purchase-upload/parse-invoice
Content-Type: multipart/form-data
Body: file (PDF file)

Response:
{
  "success": true,
  "extracted_data": {
    "supplier_name": "ABC Pharma",
    "supplier_gstin": "12ABCDE1234F1Z5",
    "invoice_number": "INV-2024-001",
    "invoice_date": "2024-01-20",
    "items": [
      {
        "product_name": "Paracetamol 500mg",
        "batch_number": "BATCH-001",
        "quantity": 100,
        "mrp": 10.00,
        "expiry_date": "2026-01-20"
      }
    ],
    "subtotal": 1000.00,
    "tax_amount": 120.00,
    "grand_total": 1120.00
  },
  "confidence_scores": {...}
}
```

### 2. Create Purchase from Parsed Data
```http
POST /api/v1/purchase-upload/create-from-parsed
Content-Type: application/json
Body: The extracted_data from above (with edits if needed)
```

## Frontend Implementation Steps

### Step 1: Add Upload Button to Purchase Entry Page

```jsx
// PurchaseEntry.jsx
import { Upload } from 'lucide-react';

function PurchaseEntry() {
  return (
    <div>
      <div className="flex justify-between mb-4">
        <h2>Create Purchase Order</h2>
        <button 
          onClick={handlePDFUpload}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded"
        >
          <Upload size={20} />
          Upload Invoice PDF
        </button>
      </div>
      {/* Rest of form */}
    </div>
  );
}
```

### Step 2: Create PDF Upload Modal

```jsx
// PDFUploadModal.jsx
import { useState } from 'react';
import { X, FileText, Loader } from 'lucide-react';

function PDFUploadModal({ isOpen, onClose, onDataExtracted }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [extractedData, setExtractedData] = useState(null);

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/v1/purchase-upload/parse-invoice', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();
      if (result.success) {
        setExtractedData(result.extracted_data);
      }
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = () => {
    onDataExtracted(extractedData);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-semibold">Upload Purchase Invoice</h3>
          <button onClick={onClose}>
            <X size={24} />
          </button>
        </div>

        {!extractedData ? (
          <div className="space-y-4">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
              <FileText size={48} className="mx-auto text-gray-400 mb-4" />
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileSelect}
                className="hidden"
                id="pdf-upload"
              />
              <label
                htmlFor="pdf-upload"
                className="cursor-pointer text-blue-600 hover:text-blue-700"
              >
                Click to select PDF invoice
              </label>
              {file && (
                <p className="mt-2 text-sm text-gray-600">
                  Selected: {file.name}
                </p>
              )}
            </div>

            <button
              onClick={handleUpload}
              disabled={!file || loading}
              className="w-full py-2 bg-blue-600 text-white rounded disabled:bg-gray-400"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader className="animate-spin" size={20} />
                  Processing...
                </span>
              ) : (
                'Upload and Extract Data'
              )}
            </button>
          </div>
        ) : (
          <ExtractedDataReview 
            data={extractedData}
            onConfirm={handleConfirm}
            onEdit={setExtractedData}
          />
        )}
      </div>
    </div>
  );
}
```

### Step 3: Create Data Review Component

```jsx
// ExtractedDataReview.jsx
function ExtractedDataReview({ data, onConfirm, onEdit }) {
  const [editedData, setEditedData] = useState(data);

  const handleItemEdit = (index, field, value) => {
    const newItems = [...editedData.items];
    newItems[index][field] = value;
    setEditedData({ ...editedData, items: newItems });
  };

  return (
    <div className="space-y-4">
      <h4 className="font-semibold">Review Extracted Data</h4>
      
      {/* Supplier Info */}
      <div className="bg-gray-50 p-4 rounded">
        <h5 className="font-medium mb-2">Supplier Information</h5>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-gray-600">Supplier Name</label>
            <input
              type="text"
              value={editedData.supplier_name}
              onChange={(e) => setEditedData({...editedData, supplier_name: e.target.value})}
              className="w-full p-2 border rounded"
            />
          </div>
          <div>
            <label className="text-sm text-gray-600">Invoice Number</label>
            <input
              type="text"
              value={editedData.invoice_number}
              onChange={(e) => setEditedData({...editedData, invoice_number: e.target.value})}
              className="w-full p-2 border rounded"
            />
          </div>
        </div>
      </div>

      {/* Items */}
      <div className="bg-gray-50 p-4 rounded">
        <h5 className="font-medium mb-2">Items</h5>
        <div className="space-y-2">
          {editedData.items.map((item, index) => (
            <div key={index} className="grid grid-cols-5 gap-2 items-center">
              <input
                type="text"
                value={item.product_name}
                onChange={(e) => handleItemEdit(index, 'product_name', e.target.value)}
                className="p-2 border rounded"
                placeholder="Product"
              />
              <input
                type="text"
                value={item.batch_number || ''}
                onChange={(e) => handleItemEdit(index, 'batch_number', e.target.value)}
                className="p-2 border rounded"
                placeholder="Batch (Auto if empty)"
              />
              <input
                type="number"
                value={item.quantity}
                onChange={(e) => handleItemEdit(index, 'quantity', e.target.value)}
                className="p-2 border rounded"
                placeholder="Qty"
              />
              <input
                type="number"
                value={item.mrp}
                onChange={(e) => handleItemEdit(index, 'mrp', e.target.value)}
                className="p-2 border rounded"
                placeholder="MRP"
              />
              <input
                type="date"
                value={item.expiry_date || ''}
                onChange={(e) => handleItemEdit(index, 'expiry_date', e.target.value)}
                className="p-2 border rounded"
                placeholder="Expiry"
              />
            </div>
          ))}
        </div>
      </div>

      {/* Totals */}
      <div className="bg-gray-50 p-4 rounded">
        <div className="flex justify-between">
          <span>Subtotal:</span>
          <span>₹{editedData.subtotal}</span>
        </div>
        <div className="flex justify-between">
          <span>Tax:</span>
          <span>₹{editedData.tax_amount}</span>
        </div>
        <div className="flex justify-between font-semibold">
          <span>Total:</span>
          <span>₹{editedData.grand_total}</span>
        </div>
      </div>

      {/* Note about auto-generation */}
      <div className="bg-blue-50 p-3 rounded text-sm text-blue-700">
        <p>💡 Leave batch number empty for automatic generation (AUTO-YYYYMMDD-PRODUCTID-XXXX)</p>
        <p>💡 Empty expiry dates will default to 2 years from today</p>
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={() => onConfirm(editedData)}
          className="flex-1 py-2 bg-green-600 text-white rounded"
        >
          Create Purchase Order
        </button>
        <button
          onClick={() => onEdit(data)}
          className="px-4 py-2 border rounded"
        >
          Reset
        </button>
      </div>
    </div>
  );
}
```

### Step 4: Integration with Purchase Form

```jsx
// In PurchaseEntry.jsx
const handlePDFData = async (extractedData) => {
  // Create purchase from parsed data
  try {
    const response = await fetch('/api/v1/purchase-upload/create-from-parsed', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(extractedData)
    });

    const result = await response.json();
    if (result.purchase_id) {
      // Redirect to purchase details or show success
      navigate(`/purchases/${result.purchase_id}`);
    }
  } catch (error) {
    console.error('Failed to create purchase:', error);
  }
};
```

## Key Features to Highlight

1. **Automatic Batch Generation**
   - If PDF doesn't have batch info, system auto-generates
   - Format: AUTO-YYYYMMDD-PRODUCTID-XXXX

2. **Smart Defaults**
   - Missing expiry dates default to 2 years
   - Missing manufacturing dates default to 30 days ago

3. **Edit Before Save**
   - Users can review and edit all extracted data
   - Add/remove items as needed
   - Fix any OCR errors

## Testing the Feature

1. Upload a pharmaceutical invoice PDF
2. Review extracted data
3. Edit if needed (or leave batch empty for auto-generation)
4. Create purchase order
5. System handles batch creation automatically

---

This implementation leverages the backend's intelligent batch handling while giving users full control over the data.