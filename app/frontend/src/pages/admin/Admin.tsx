import { useState, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import {
    Stack,
    TextField,
    PrimaryButton,
    DefaultButton,
    MessageBar,
    MessageBarType,
    Spinner,
    SpinnerSize,
    DetailsList,
    DetailsListLayoutMode,
    SelectionMode,
    IColumn,
    IconButton,
    Dialog,
    DialogType,
    DialogFooter
} from "@fluentui/react";
import styles from "./Admin.module.css";
import {
    listAgentsApi,
    createAgentApi,
    deleteAgentApi,
    listAgentDocumentsApi,
    uploadAgentDocumentApi,
    deleteAgentDocumentApi,
    Agent,
    AgentDocument
} from "../../api";

const Admin = () => {
    const { t } = useTranslation();
    const [agents, setAgents] = useState<Agent[]>([]);
    const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
    const [documents, setDocuments] = useState<AgentDocument[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    // Form states
    const [newAgentName, setNewAgentName] = useState("");
    const [newAgentDescription, setNewAgentDescription] = useState("");
    const [isCreating, setIsCreating] = useState(false);

    // Delete confirmation
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [agentToDelete, setAgentToDelete] = useState<Agent | null>(null);

    // File upload
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [uploading, setUploading] = useState(false);

    // Load agents on mount
    useEffect(() => {
        loadAgents();
    }, []);

    // Load documents when agent is selected
    useEffect(() => {
        if (selectedAgent) {
            loadDocuments(selectedAgent.id);
        } else {
            setDocuments([]);
        }
    }, [selectedAgent]);

    const loadAgents = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await listAgentsApi();
            setAgents(data);
        } catch (e: any) {
            setError(e.message || "Erreur lors du chargement des agents");
        } finally {
            setLoading(false);
        }
    };

    const loadDocuments = async (agentId: string) => {
        try {
            const data = await listAgentDocumentsApi(agentId);
            setDocuments(data);
        } catch (e: any) {
            setError(e.message || "Erreur lors du chargement des documents");
        }
    };

    const handleCreateAgent = async () => {
        if (!newAgentName.trim()) {
            setError("Le nom de l'agent est requis");
            return;
        }

        setIsCreating(true);
        setError(null);
        try {
            await createAgentApi(newAgentName, newAgentDescription);
            setSuccess(`Agent "${newAgentName}" cree avec succes`);
            setNewAgentName("");
            setNewAgentDescription("");
            await loadAgents();
        } catch (e: any) {
            setError(e.message || "Erreur lors de la creation de l'agent");
        } finally {
            setIsCreating(false);
        }
    };

    const handleDeleteAgent = async () => {
        if (!agentToDelete) return;

        setError(null);
        try {
            await deleteAgentApi(agentToDelete.id);
            setSuccess(`Agent "${agentToDelete.name}" supprime avec succes`);
            if (selectedAgent?.id === agentToDelete.id) {
                setSelectedAgent(null);
            }
            await loadAgents();
        } catch (e: any) {
            setError(e.message || "Erreur lors de la suppression de l'agent");
        } finally {
            setDeleteDialogOpen(false);
            setAgentToDelete(null);
        }
    };

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!selectedAgent || !e.target.files || e.target.files.length === 0) return;

        setUploading(true);
        setError(null);
        try {
            for (const file of Array.from(e.target.files)) {
                await uploadAgentDocumentApi(selectedAgent.id, file);
            }
            setSuccess(`Document(s) uploade(s) avec succes`);
            await loadDocuments(selectedAgent.id);
            await loadAgents(); // Refresh document count
        } catch (e: any) {
            setError(e.message || "Erreur lors de l'upload");
        } finally {
            setUploading(false);
            if (fileInputRef.current) {
                fileInputRef.current.value = "";
            }
        }
    };

    const handleDeleteDocument = async (doc: AgentDocument) => {
        if (!selectedAgent) return;

        setError(null);
        try {
            await deleteAgentDocumentApi(selectedAgent.id, doc.id);
            setSuccess(`Document "${doc.filename}" supprime`);
            await loadDocuments(selectedAgent.id);
            await loadAgents();
        } catch (e: any) {
            setError(e.message || "Erreur lors de la suppression du document");
        }
    };

    const agentColumns: IColumn[] = [
        {
            key: "name",
            name: "Nom",
            fieldName: "name",
            minWidth: 150,
            maxWidth: 200,
            isResizable: true
        },
        {
            key: "description",
            name: "Description",
            fieldName: "description",
            minWidth: 200,
            maxWidth: 300,
            isResizable: true
        },
        {
            key: "status",
            name: "Statut",
            fieldName: "status",
            minWidth: 80,
            maxWidth: 100
        },
        {
            key: "document_count",
            name: "Documents",
            fieldName: "document_count",
            minWidth: 80,
            maxWidth: 100
        },
        {
            key: "actions",
            name: "Actions",
            minWidth: 100,
            maxWidth: 150,
            onRender: (item: Agent) => (
                <Stack horizontal tokens={{ childrenGap: 5 }}>
                    <IconButton
                        iconProps={{ iconName: "View" }}
                        title="Voir les documents"
                        onClick={() => setSelectedAgent(item)}
                    />
                    <IconButton
                        iconProps={{ iconName: "Delete" }}
                        title="Supprimer"
                        onClick={() => {
                            setAgentToDelete(item);
                            setDeleteDialogOpen(true);
                        }}
                    />
                </Stack>
            )
        }
    ];

    const documentColumns: IColumn[] = [
        {
            key: "filename",
            name: "Fichier",
            fieldName: "filename",
            minWidth: 200,
            maxWidth: 300,
            isResizable: true
        },
        {
            key: "status",
            name: "Statut",
            fieldName: "status",
            minWidth: 100,
            maxWidth: 120,
            onRender: (item: AgentDocument) => (
                <span className={item.status === "indexed" ? styles.statusIndexed : item.status === "error" ? styles.statusError : styles.statusPending}>
                    {item.status}
                </span>
            )
        },
        {
            key: "size",
            name: "Taille",
            fieldName: "size",
            minWidth: 80,
            maxWidth: 100,
            onRender: (item: AgentDocument) => formatFileSize(item.size)
        },
        {
            key: "actions",
            name: "Actions",
            minWidth: 80,
            maxWidth: 100,
            onRender: (item: AgentDocument) => (
                <IconButton
                    iconProps={{ iconName: "Delete" }}
                    title="Supprimer"
                    onClick={() => handleDeleteDocument(item)}
                />
            )
        }
    ];

    const formatFileSize = (bytes: number): string => {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    };

    return (
        <div className={styles.container}>
            <h1 className={styles.title}>Administration des RAGs</h1>

            {error && (
                <MessageBar
                    messageBarType={MessageBarType.error}
                    onDismiss={() => setError(null)}
                    dismissButtonAriaLabel="Fermer"
                >
                    {error}
                </MessageBar>
            )}

            {success && (
                <MessageBar
                    messageBarType={MessageBarType.success}
                    onDismiss={() => setSuccess(null)}
                    dismissButtonAriaLabel="Fermer"
                >
                    {success}
                </MessageBar>
            )}

            <div className={styles.section}>
                <h2>Creer un nouvel agent RAG</h2>
                <Stack horizontal tokens={{ childrenGap: 10 }} verticalAlign="end">
                    <TextField
                        label="Nom"
                        value={newAgentName}
                        onChange={(_, v) => setNewAgentName(v || "")}
                        placeholder="Ex: RAG IT, RAG Juridique..."
                        styles={{ root: { width: 200 } }}
                    />
                    <TextField
                        label="Description"
                        value={newAgentDescription}
                        onChange={(_, v) => setNewAgentDescription(v || "")}
                        placeholder="Description de l'agent"
                        styles={{ root: { width: 300 } }}
                    />
                    <PrimaryButton
                        text="Creer"
                        onClick={handleCreateAgent}
                        disabled={isCreating || !newAgentName.trim()}
                    />
                    {isCreating && <Spinner size={SpinnerSize.small} />}
                </Stack>
            </div>

            <div className={styles.section}>
                <h2>Agents RAG existants</h2>
                {loading ? (
                    <Spinner size={SpinnerSize.large} label="Chargement..." />
                ) : agents.length === 0 ? (
                    <p>Aucun agent RAG cree. Creez-en un ci-dessus.</p>
                ) : (
                    <DetailsList
                        items={agents}
                        columns={agentColumns}
                        layoutMode={DetailsListLayoutMode.justified}
                        selectionMode={SelectionMode.none}
                    />
                )}
            </div>

            {selectedAgent && (
                <div className={styles.section}>
                    <Stack horizontal horizontalAlign="space-between" verticalAlign="center">
                        <h2>Documents de "{selectedAgent.name}"</h2>
                        <DefaultButton
                            text="Fermer"
                            onClick={() => setSelectedAgent(null)}
                        />
                    </Stack>

                    <Stack horizontal tokens={{ childrenGap: 10 }} className={styles.uploadSection}>
                        <input
                            type="file"
                            ref={fileInputRef}
                            onChange={handleFileUpload}
                            multiple
                            accept=".pdf,.docx,.txt,.md,.html,.csv"
                            style={{ display: "none" }}
                        />
                        <PrimaryButton
                            text="Uploader des documents"
                            iconProps={{ iconName: "Upload" }}
                            onClick={() => fileInputRef.current?.click()}
                            disabled={uploading}
                        />
                        {uploading && <Spinner size={SpinnerSize.small} label="Upload en cours..." />}
                    </Stack>

                    {documents.length === 0 ? (
                        <p>Aucun document dans cet agent. Uploadez des documents ci-dessus.</p>
                    ) : (
                        <DetailsList
                            items={documents}
                            columns={documentColumns}
                            layoutMode={DetailsListLayoutMode.justified}
                            selectionMode={SelectionMode.none}
                        />
                    )}
                </div>
            )}

            <Dialog
                hidden={!deleteDialogOpen}
                onDismiss={() => setDeleteDialogOpen(false)}
                dialogContentProps={{
                    type: DialogType.normal,
                    title: "Confirmer la suppression",
                    subText: `Etes-vous sur de vouloir supprimer l'agent "${agentToDelete?.name}" ? Cette action supprimera egalement tous les documents associes.`
                }}
            >
                <DialogFooter>
                    <PrimaryButton onClick={handleDeleteAgent} text="Supprimer" />
                    <DefaultButton onClick={() => setDeleteDialogOpen(false)} text="Annuler" />
                </DialogFooter>
            </Dialog>
        </div>
    );
};

export default Admin;
