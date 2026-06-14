#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdlib.h>

#ifdef _OPENMP
    #include <omp.h>
#else
    #define omp_get_thread_num() 0
    #define omp_get_max_threads() 1
#endif

#define MAX_THREADS 4
#define MAX_MATCHES_PER_THREAD 5000 
#define MAX_LOOKAHEAD 256 

typedef struct {
    int rule_idx;
    size_t start;
    size_t end;
} MatchRecord;

void redact_matrix_parallel(char* text, size_t length, int requested_threads, int* dfa_matrix, const char** c_tags, Py_ssize_t matrix_byte_len, MatchRecord* all_threads_matches, int* match_counts) {
    int num_threads = (requested_threads > MAX_THREADS) ? MAX_THREADS : requested_threads;
    int max_safe_index = (int)(matrix_byte_len / sizeof(int));
    
    // PASS 1: MAP (Read-Only Lock-Free Scanning)
    #pragma omp parallel num_threads(num_threads)
    {
        int tid = omp_get_thread_num();
        size_t chunk_size = length / num_threads;
        size_t start = tid * chunk_size;
        size_t end = (tid == num_threads - 1) ? length : (start + chunk_size);
        
        size_t scan_end = end + MAX_LOOKAHEAD;
        if (scan_end > length) scan_end = length;
        
        int state = 0;
        size_t start_idx = start;
        
        MatchRecord* local_matches = &all_threads_matches[tid * MAX_MATCHES_PER_THREAD];
        int local_count = 0;

        for (size_t i = start; i < scan_end; i++) {
            unsigned char c = (unsigned char)text[i];
            int lookup_state = (state < 0) ? -state : state;
            int lookup_index = (lookup_state * 256) + c;
            
            if (lookup_index >= max_safe_index || lookup_index < 0) {
                state = 0;
                continue;
            }
            
            int next_state = dfa_matrix[lookup_index];

            // FAANG FIX: Failure Link Re-evaluation.
            // If the current path dies, we DO NOT swallow the character.
            // We instantly re-evaluate it against the root state (0).
            if (next_state == 0 && lookup_state != 0) {
                next_state = dfa_matrix[c]; // equivalent to dfa_matrix[0 * 256 + c]
                if (next_state != 0) {
                    start_idx = i; // It started a new secret! Update start index immediately.
                }
            } else if (state == 0 && next_state != 0) {
                start_idx = i; // Normal start
            }

            if (next_state < 0) {
                int terminal_row = -next_state;
                if (state >= 0) {
                    if (start_idx >= start && start_idx < end) {
                        if (local_count < MAX_MATCHES_PER_THREAD) {
                            local_matches[local_count].rule_idx = terminal_row;
                            local_matches[local_count].start = start_idx;
                            local_matches[local_count].end = i;
                            local_count++;
                        }
                    }
                }
            }
            
            if (i >= end && next_state == 0) break;
            
            state = next_state;
        }
        match_counts[tid] = local_count;
    }

    // PASS 2: REDUCE & MUTATE (Deferred Write)
    for (int t = 0; t < num_threads; t++) {
        for (int m = 0; m < match_counts[t]; m++) {
            MatchRecord record = all_threads_matches[t * MAX_MATCHES_PER_THREAD + m];
            size_t tag_len = strlen(c_tags[record.rule_idx]);
            for (size_t j = record.start; j <= record.end; j++) {
                text[j] = ((j - record.start) < tag_len) ? c_tags[record.rule_idx][j - record.start] : '*';
            }
        }
    }
}

static PyObject* py_redact(PyObject* self, PyObject* args) {
    Py_buffer text_buf; 
    int num_threads; 
    Py_buffer matrix_buf;
    PyObject* tags_tuple;
    PyObject* matches;
    
    if (!PyArg_ParseTuple(args, "w*iy*O!O!", &text_buf, &num_threads, &matrix_buf, &PyTuple_Type, &tags_tuple, &PyList_Type, &matches)) return NULL;

    char* mutable_text = (char*)text_buf.buf;
    size_t length = text_buf.len;

    Py_ssize_t num_tags = PyTuple_Size(tags_tuple);
    const char** c_tags = (const char**)PyMem_Malloc(num_tags * sizeof(char*));
    for (Py_ssize_t i = 0; i < num_tags; i++) c_tags[i] = PyUnicode_AsUTF8(PyTuple_GetItem(tags_tuple, i));
    
    int* dfa_matrix = (int*)matrix_buf.buf;
    MatchRecord* all_threads_matches = (MatchRecord*)malloc(sizeof(MatchRecord) * MAX_MATCHES_PER_THREAD * MAX_THREADS);
    int match_counts[MAX_THREADS] = {0};

    Py_BEGIN_ALLOW_THREADS
    redact_matrix_parallel(mutable_text, length, num_threads, dfa_matrix, c_tags, matrix_buf.len, all_threads_matches, match_counts);
    Py_END_ALLOW_THREADS

    for (int t = 0; t < MAX_THREADS; t++) {
        for (int m = 0; m < match_counts[t]; m++) {
            MatchRecord record = all_threads_matches[(t * MAX_MATCHES_PER_THREAD) + m];
            PyObject* match = Py_BuildValue("{s:s, s:n, s:n}", "rule", c_tags[record.rule_idx], "start", (Py_ssize_t)record.start, "end", (Py_ssize_t)record.end);
            PyList_Append(matches, match);
            Py_DECREF(match);
        }
    }

    PyMem_Free((void*)c_tags);
    free(all_threads_matches);
    PyBuffer_Release(&matrix_buf);
    PyBuffer_Release(&text_buf);
    
    Py_RETURN_TRUE;
}

static PyMethodDef MatrixRedactMethods[] = {
    {"redact", py_redact, METH_VARARGS, "Two-Pass Boundary-Safe Enterprise DFA."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef matrixredactmodule = {
    PyModuleDef_HEAD_INIT, "guardog_core", NULL, -1, MatrixRedactMethods
};

PyMODINIT_FUNC PyInit_guardog_core(void) {
    return PyModule_Create(&matrixredactmodule);
}