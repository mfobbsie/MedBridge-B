interface ErrorStateProps {
    error?: string;
}


export const ErrorState = ({error = "Something went wrong. Please try again."}: ErrorStateProps) => {
    return (
        <h3 className="error">Error:{error}</h3>
    )
}