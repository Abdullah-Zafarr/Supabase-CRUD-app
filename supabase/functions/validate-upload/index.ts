import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type, x-edge-function-secret",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

const DEFAULT_BUCKET = "documents";
const MAX_FILE_SIZE_BYTES = Number(
  Deno.env.get("MAX_FILE_SIZE_BYTES") ?? 10 * 1024 * 1024,
);
const ALLOWED_MIME_TYPES = new Set([
  "application/json",
  "application/pdf",
  "image/gif",
  "image/jpeg",
  "image/png",
  "image/webp",
  "text/csv",
  "text/plain",
]);

type UploadPayload = {
  record_id?: string;
  bucket?: string;
  path?: string;
  previous_path?: string;
  mode?: "create" | "replace";
  original_name?: string;
  content_type?: string;
  description?: string | null;
  uploaded_by?: string;
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

function isSafePath(path: string): boolean {
  if (!path || path.startsWith("/") || path.includes("\\")) return false;
  return path.split("/").every((part) => part.length > 0 && part !== "." && part !== "..");
}

function startsWithBytes(bytes: Uint8Array, signature: number[]): boolean {
  return signature.every((value, index) => bytes[index] === value);
}

function detectMime(bytes: Uint8Array, declared: string): string | null {
  if (startsWithBytes(bytes, [0xff, 0xd8, 0xff])) return "image/jpeg";
  if (startsWithBytes(bytes, [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])) {
    return "image/png";
  }
  const header = new TextDecoder().decode(bytes.slice(0, 8));
  if (header.startsWith("GIF87a") || header.startsWith("GIF89a")) return "image/gif";
  const riff = new TextDecoder().decode(bytes.slice(0, 4));
  const webp = new TextDecoder().decode(bytes.slice(8, 12));
  if (riff === "RIFF" && webp === "WEBP") return "image/webp";
  const pdfHeader = new TextDecoder().decode(bytes.slice(0, 5));
  if (pdfHeader === "%PDF-") return "application/pdf";

  // Text formats have no universal magic number. Requiring valid UTF-8 and an
  // allowed declared type still prevents arbitrary binary files from passing.
  try {
    new TextDecoder("utf-8", { fatal: true }).decode(bytes);
    if (ALLOWED_MIME_TYPES.has(declared) && declared.startsWith("text/")) return declared;
    if (declared === "application/json") return declared;
  } catch {
    return null;
  }
  return null;
}

async function sha256Hex(bytes: Uint8Array): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)]
    .map((value) => value.toString(16).padStart(2, "0"))
    .join("");
}

async function removeObject(admin: ReturnType<typeof createClient>, bucket: string, path: string) {
  const { error } = await admin.storage.from(bucket).remove([path]);
  if (error) console.error("Could not remove rejected object:", error.message);
}

Deno.serve(async (request) => {
  if (request.method === "OPTIONS") return new Response("ok", { headers: corsHeaders });
  if (request.method !== "POST") return jsonResponse({ error: "POST is required" }, 405);

  const expectedSecret = Deno.env.get("EDGE_FUNCTION_SECRET");
  if (!expectedSecret || request.headers.get("x-edge-function-secret") !== expectedSecret) {
    return jsonResponse({ error: "Unauthorized" }, 401);
  }

  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const serviceKey =
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? Deno.env.get("SUPABASE_SECRET_KEY");
  if (!supabaseUrl || !serviceKey) {
    return jsonResponse({ error: "Function server configuration is incomplete" }, 500);
  }

  let payload: UploadPayload;
  try {
    payload = await request.json();
  } catch {
    return jsonResponse({ error: "Request body must be valid JSON" }, 400);
  }

  const recordId = payload.record_id;
  const bucket = payload.bucket ?? DEFAULT_BUCKET;
  const path = payload.path;
  const mode = payload.mode ?? "create";
  const declaredType = payload.content_type ?? "application/octet-stream";
  if (!recordId || !path || !isSafePath(path) || bucket !== DEFAULT_BUCKET) {
    return jsonResponse({ error: "record_id, bucket, and a safe path are required" }, 400);
  }
  if (!ALLOWED_MIME_TYPES.has(declaredType)) {
    await removeObject(createClient(supabaseUrl, serviceKey), bucket, path);
    return jsonResponse({ error: `MIME type is not allowed: ${declaredType}` }, 422);
  }

  const admin = createClient(supabaseUrl, serviceKey, {
    auth: { autoRefreshToken: false, persistSession: false },
  });
  const { data: record, error: recordError } = await admin
    .from("file_records")
    .select("*")
    .eq("id", recordId)
    .maybeSingle();
  if (recordError || !record) {
    await removeObject(admin, bucket, path);
    return jsonResponse({ error: "Metadata record was not found" }, 404);
  }
  if (record.bucket_name !== bucket || (mode === "create" && record.storage_path !== path)) {
    await removeObject(admin, bucket, path);
    return jsonResponse({ error: "Record and Storage object do not match" }, 409);
  }

  const { data: file, error: downloadError } = await admin.storage.from(bucket).download(path);
  if (downloadError || !file) {
    return jsonResponse({ error: downloadError?.message ?? "Could not read uploaded file" }, 422);
  }

  const bytes = new Uint8Array(await file.arrayBuffer());
  const actualType = detectMime(bytes, declaredType);
  if (bytes.byteLength > MAX_FILE_SIZE_BYTES || !actualType || !ALLOWED_MIME_TYPES.has(actualType)) {
    const message = !actualType
      ? "The file signature or text encoding is not supported"
      : `File exceeds ${MAX_FILE_SIZE_BYTES} bytes or has an invalid type`;
    await removeObject(admin, bucket, path);
    const update = mode === "create"
      ? { status: "rejected", validation_error: message }
      : { validation_error: message };
    await admin.from("file_records").update(update).eq("id", recordId);
    return jsonResponse({ error: message }, 422);
  }

  const checksum = await sha256Hex(bytes);
  const metadata = {
    scanned_at: new Date().toISOString(),
    detected_content_type: actualType,
    size_bytes: bytes.byteLength,
    checksum_sha256: checksum,
    validation: "passed",
  };
  const update = {
    bucket_name: bucket,
    storage_path: path,
    original_name: payload.original_name ?? record.original_name,
    uploaded_by: payload.uploaded_by ?? record.uploaded_by,
    content_type: actualType,
    size_bytes: bytes.byteLength,
    checksum_sha256: checksum,
    description: payload.description ?? record.description,
    status: "active",
    validation_error: null,
  };
  const { data: updated, error: updateError } = await admin
    .from("file_records")
    .update(update)
    .eq("id", recordId)
    .select("*")
    .single();
  if (updateError) {
    await removeObject(admin, bucket, path);
    return jsonResponse({ error: updateError.message }, 500);
  }

  if (mode === "replace" && payload.previous_path && payload.previous_path !== path) {
    await removeObject(admin, bucket, payload.previous_path);
  }

  return jsonResponse({
    message: "File validated and metadata generated",
    record: updated,
    storage_metadata: metadata,
  });
});
