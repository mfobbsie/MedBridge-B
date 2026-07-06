
export type EmptyStateProps<T> = {
    data: T[];
    itemName?: string;
}


export function EmptyState<T>({ data, itemName = "items" }: EmptyStateProps<T>) {

    if (data.length > 0) {
        return null;
    }

    return (
        <div className="empty-state">
            No {itemName} found.
        </div>
    );
}