/// <reference path="../pb_data/types.d.ts" />

migrate(
  (app) => {
    // ── Extend the built-in "users" collection with a role field ──
    const users = app.findCollectionByNameOrId("users");
    users.fields.push(
      new Field({
        name: "role",
        type: "select",
        required: false,
        values: ["user", "superuser"],
      })
    );
    app.save(users);

    // ── Create "rag_configs" collection ──
    const ragConfigs = new Collection({
      name: "rag_configs",
      type: "base",
      listRule: "@request.auth.role = 'superuser'",
      viewRule: "@request.auth.role = 'superuser'",
      createRule: "@request.auth.role = 'superuser'",
      updateRule: "@request.auth.role = 'superuser'",
      deleteRule: "@request.auth.role = 'superuser'",
    });
    // General
    ragConfigs.fields.push(new Field({ name: "name", type: "text", required: true }));
    ragConfigs.fields.push(new Field({ name: "description", type: "text", required: false }));
    ragConfigs.fields.push(new Field({ name: "retrieval_backend", type: "select", required: true, values: ["none", "rag_store", "vertex_search", "vector_search"] }));
    ragConfigs.fields.push(new Field({ name: "is_active", type: "bool", required: false }));
    // LLM
    ragConfigs.fields.push(new Field({ name: "llm_model", type: "text", required: false }));
    ragConfigs.fields.push(new Field({ name: "temperature", type: "number", required: false, min: 0, max: 2 }));
    ragConfigs.fields.push(new Field({ name: "top_k", type: "number", required: false, min: 1, max: 100 }));
    ragConfigs.fields.push(new Field({ name: "max_output_tokens", type: "number", required: false, min: 1, max: 65536 }));
    ragConfigs.fields.push(new Field({ name: "system_prompt", type: "text", required: false }));
    ragConfigs.fields.push(new Field({ name: "top_p", type: "number", required: false, min: 0, max: 1 }));
    // RAG Store
    ragConfigs.fields.push(new Field({ name: "rag_corpus_name", type: "text", required: false }));
    ragConfigs.fields.push(new Field({ name: "rag_similarity_top_k", type: "number", required: false, min: 1, max: 100 }));
    ragConfigs.fields.push(new Field({ name: "rag_vector_distance_threshold", type: "number", required: false, min: 0, max: 1 }));
    // Vertex AI Search
    ragConfigs.fields.push(new Field({ name: "vs_serving_config", type: "text", required: false }));
    ragConfigs.fields.push(new Field({ name: "vs_datastore", type: "text", required: false }));
    ragConfigs.fields.push(new Field({ name: "vs_filter", type: "text", required: false }));
    ragConfigs.fields.push(new Field({ name: "vs_order_by", type: "text", required: false }));
    ragConfigs.fields.push(new Field({ name: "vs_boost_spec", type: "json", required: false }));
    ragConfigs.fields.push(new Field({ name: "vs_query_expansion", type: "bool", required: false }));
    ragConfigs.fields.push(new Field({ name: "vs_spell_correction", type: "bool", required: false }));
    ragConfigs.fields.push(new Field({ name: "vs_summary_result_count", type: "number", required: false, min: 0, max: 10 }));
    ragConfigs.fields.push(new Field({ name: "vs_snippet_result_count", type: "number", required: false, min: 0, max: 5 }));
    // Vector Search
    ragConfigs.fields.push(new Field({ name: "vec_index_endpoint", type: "text", required: false }));
    ragConfigs.fields.push(new Field({ name: "vec_deployed_index_id", type: "text", required: false }));
    ragConfigs.fields.push(new Field({ name: "vec_embedding_model", type: "text", required: false }));
    ragConfigs.fields.push(new Field({ name: "vec_approx_neighbor_count", type: "number", required: false, min: 1, max: 1000 }));
    ragConfigs.fields.push(new Field({ name: "vec_fraction_leaf_nodes", type: "number", required: false, min: 0, max: 1 }));
    ragConfigs.fields.push(new Field({ name: "vec_filter_restricts", type: "json", required: false }));
    ragConfigs.fields.push(new Field({ name: "vec_return_full_datapoint", type: "bool", required: false }));
    app.save(ragConfigs);

    // ── Create "chat_history" collection ──
    const chatHistory = new Collection({
      name: "chat_history",
      type: "base",
      listRule: "@request.auth.id = user",
      viewRule: "@request.auth.id = user",
      createRule: "@request.auth.id != ''",
      updateRule: null,
      deleteRule: "@request.auth.role = 'superuser'",
    });
    chatHistory.fields.push(new Field({ name: "user", type: "relation", required: true, collectionId: users.id, maxSelect: 1 }));
    chatHistory.fields.push(new Field({ name: "query", type: "text", required: true }));
    chatHistory.fields.push(new Field({ name: "answer", type: "text", required: false }));
    chatHistory.fields.push(new Field({ name: "backend", type: "select", required: false, values: ["none", "rag_store", "vertex_search", "vector_search"] }));
    chatHistory.fields.push(new Field({ name: "sources", type: "json", required: false }));
    chatHistory.fields.push(new Field({ name: "config_id", type: "text", required: false }));
    app.save(chatHistory);
  },
  (app) => {
    const chatHistory = app.findCollectionByNameOrId("chat_history");
    app.delete(chatHistory);

    const ragConfigs = app.findCollectionByNameOrId("rag_configs");
    app.delete(ragConfigs);
  }
);
